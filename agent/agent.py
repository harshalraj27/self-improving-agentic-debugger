from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from agent import states
from agent.llm_agent import query_debugger
from agent.memory import DebuggingMemory
from agent.prompts import SYSTEM_PROMPT, generate_user_prompt
from agent.states import State, TransitionEvent
from agent.telemetry import TelemetryTracer
from core.factory import RunnerFactory
from core.patcher import apply_patch
from core.runners.base import ExecutionResult


class Agent:
    def __init__(self, file_path: str, max_retries: int = 5, job_id: str | None = None) -> None:
        self.file_path = file_path
        self.max_retries = max_retries
        self.job_id = job_id or str(uuid.uuid4())

        self.state = State.READY
        self.current_retry = 0
        self.last_run_result: ExecutionResult | None = None

        self.memory = DebuggingMemory()
        self.telemetry = TelemetryTracer(self.job_id)
        self.initial_code_snapshot = Path(file_path).read_text(encoding="utf-8")

        self._user_prompt = ""
        self._raw_llm_output = ""
        self._terminated_successfully = False
        self._initial_error_trace: str | None = None

    def _transition(self, event: TransitionEvent) -> None:
        self.state = states.validate_and_get_next(self.state, event)

    @staticmethod
    def _extract_error_type(result: ExecutionResult) -> str | None:
        if result.error:
            return result.error.split(":", 1)[0].strip() if ":" in result.error else result.error
        if result.stderr:
            lines = result.stderr.strip().splitlines()
            if lines and ":" in lines[-1]:
                return lines[-1].split(":", 1)[0].strip()
        return None

    @staticmethod
    def _resolve_language(file_path: str) -> str:
        suffix = Path(file_path).suffix.lower()
        if suffix == ".py":
            return "python"
        if suffix == ".cpp":
            return "cpp"
        raise ValueError(f"Unsupported language extension: {suffix}")

    def run(self) -> bool:
        while self.state is not State.TERMINATED:
            print(f"[FSM State] -> {self.state.name} (Retry: {self.current_retry}/{self.max_retries})")

            self.telemetry.start_state_capture(self.state.name, self.current_retry)
            current_metadata: dict[str, Any] = {}

            match self.state:
                case State.READY:
                    print(f"[READY] Running sandbox execution for {Path(self.file_path).name}")
                    runner = RunnerFactory.get_runner(self.file_path)
                    self.last_run_result = runner.execute()

                    if self.last_run_result:
                        current_metadata = {
                            "exit_code": self.last_run_result.exit_code,
                            "stage": self.last_run_result.stage,
                        }
                    self._transition(TransitionEvent.CONTINUE)

                case State.OBSERVED:
                    if self.last_run_result is None:
                        self._transition(TransitionEvent.HALT)
                        continue

                    result = self.last_run_result
                    error_type = self._extract_error_type(result)

                    if result.success:
                        print(f"[OBSERVED] success=True exit_code={result.exit_code} stage={result.stage}")
                    else:
                        print(
                            f"[OBSERVED] success=False exit_code={result.exit_code} stage={result.stage} error_type={error_type}")

                    current_metadata = {
                        "success": result.success,
                        "exit_code": result.exit_code,
                        "error_type": error_type,
                    }

                    if result.success:
                        if self.current_retry > 0 and self._initial_error_trace is not None:
                            language = self._resolve_language(self.file_path)
                            patched_source = Path(self.file_path).read_text(encoding="utf-8")
                            self.memory.add_experience(self._initial_error_trace, language, patched_source)

                        self._terminated_successfully = True
                        self._transition(TransitionEvent.SUCCESS)
                    elif self.current_retry >= self.max_retries:
                        self._transition(TransitionEvent.HALT)
                    else:
                        if self._initial_error_trace is None:
                            self._initial_error_trace = result.stderr
                        self._transition(TransitionEvent.CONTINUE)

                case State.EVALUATED:
                    if self.last_run_result is None:
                        self._transition(TransitionEvent.HALT)
                        continue

                    source_code = Path(self.file_path).read_text(encoding="utf-8")
                    language = self._resolve_language(self.file_path)
                    past_fix = self.memory.query_memory(self.last_run_result.stderr, language)

                    has_rag_hit = bool(past_fix)
                    current_metadata = {"rag_memory_hit": has_rag_hit}

                    if has_rag_hit:
                        print("[EVALUATED] ChromaDB RAG hit — past trajectory found")
                    else:
                        print("[EVALUATED] Cold cache — querying base model")

                    self._user_prompt = generate_user_prompt(source_code, self.last_run_result, past_fix=past_fix)
                    self._transition(TransitionEvent.CONTINUE)

                case State.ACTION_SELECTED:
                    print("[ACTION_SELECTED] Querying local Ollama (qwen2.5-coder:7b)")
                    self._raw_llm_output = query_debugger(SYSTEM_PROMPT, self._user_prompt)

                    language = self._resolve_language(self.file_path)
                    has_rag_hit = False
                    if self.last_run_result and self.last_run_result.stderr:
                        has_rag_hit = bool(self.memory.query_memory(self.last_run_result.stderr, language))

                    current_metadata = {
                        "prompt": self._user_prompt,
                        "output": self._raw_llm_output,
                        "rag_memory_hit": has_rag_hit
                    }
                    self._transition(TransitionEvent.CONTINUE)

                case State.ACTED:
                    patch_applied = apply_patch(self.file_path, self._raw_llm_output)
                    if not patch_applied:
                        print("[ACTED] Patcher failed — invalid markdown format")
                        current_metadata = {"patch_applied": False}
                        self._transition(TransitionEvent.HALT)
                    else:
                        print(f"[ACTED] Patch successfully written to {Path(self.file_path).name}")
                        current_metadata = {"patch_applied": True}
                        self.current_retry += 1
                        self._transition(TransitionEvent.CONTINUE)

                case State.TERMINATED:
                    break

            self.telemetry.stop_state_capture(current_metadata)

        final_code = Path(self.file_path).read_text(encoding="utf-8")
        self.telemetry.finalize_trace(self._terminated_successfully, self.initial_code_snapshot, final_code)

        return self._terminated_successfully