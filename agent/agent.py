from __future__ import annotations

from pathlib import Path

from agent import states
from agent.llm_agent import query_debugger
from agent.memory import DebuggingMemory
from agent.prompts import SYSTEM_PROMPT, generate_user_prompt
from agent.states import State, TransitionEvent
from core.factory import RunnerFactory
from core.patcher import apply_patch
from core.runners.base import ExecutionResult


class Agent:
    def __init__(self, file_path: str, max_retries: int = 5) -> None:
        self.file_path: str = file_path
        self.max_retries: int = max_retries
        self.state: State = State.READY
        self.current_retry: int = 0
        self.last_run_result: ExecutionResult | None = None
        self.memory: DebuggingMemory = DebuggingMemory()
        self._user_prompt: str = ""
        self._raw_llm_output: str = ""
        self._terminated_successfully: bool = False
        self._initial_error_trace: str | None = None

    def _transition(self, event: TransitionEvent) -> None:
        self.state = states.validate_and_get_next(self.state, event)

    @staticmethod
    def _extract_error_type(result: ExecutionResult) -> str | None:
        if result.error:
            if ":" in result.error:
                return result.error.split(":", 1)[0].strip()
            return result.error
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
        raise ValueError(f"Unsupported language for: {file_path}")

    def run(self) -> bool:
        while self.state is not State.TERMINATED:
            print(
                f"🔄 [FSM State] -> {self.state.name} "
                f"(Retry: {self.current_retry}/{self.max_retries})"
            )
            match self.state:
                case State.READY:
                    print(
                        f"🐳 [READY] Initializing Docker sandbox and executing "
                        f"{Path(self.file_path).name}"
                    )
                    runner = RunnerFactory.get_runner(self.file_path)
                    self.last_run_result = runner.execute()
                    self._transition(TransitionEvent.CONTINUE)

                case State.OBSERVED:
                    if self.last_run_result is None:
                        self._transition(TransitionEvent.HALT)
                        continue
                    result = self.last_run_result
                    if result.success:
                        print(
                            f"📊 [OBSERVED] success={result.success} "
                            f"exit_code={result.exit_code} stage={result.stage}"
                        )
                    else:
                        error_type = self._extract_error_type(result)
                        print(
                            f"📊 [OBSERVED] success={result.success} "
                            f"exit_code={result.exit_code} stage={result.stage} "
                            f"error_type={error_type} line_number={result.line_number}"
                        )
                    if self.last_run_result.success:
                        if (
                            self.current_retry > 0
                            and self._initial_error_trace is not None
                        ):
                            language = self._resolve_language(self.file_path)
                            patched_source = Path(self.file_path).read_text(
                                encoding="utf-8"
                            )
                            self.memory.add_experience(
                                self._initial_error_trace,
                                language,
                                patched_source,
                            )
                        self._terminated_successfully = True
                        self._transition(TransitionEvent.SUCCESS)
                    elif self.current_retry >= self.max_retries:
                        self._transition(TransitionEvent.HALT)
                    else:
                        if self._initial_error_trace is None:
                            self._initial_error_trace = self.last_run_result.stderr
                        self._transition(TransitionEvent.CONTINUE)

                case State.EVALUATED:
                    source_code = Path(self.file_path).read_text(encoding="utf-8")
                    if self.last_run_result is None:
                        self._transition(TransitionEvent.HALT)
                        continue
                    language = self._resolve_language(self.file_path)
                    past_fix = self.memory.query_memory(
                        self.last_run_result.stderr, language
                    )
                    if past_fix:
                        print(
                            "🧠 [EVALUATED] ChromaDB RAG hit — similar past fix retrieved"
                        )
                    else:
                        print("🧠 [EVALUATED] Cold cache — no matching trajectory in memory")
                    self._user_prompt = generate_user_prompt(
                        source_code,
                        self.last_run_result,
                        past_fix=past_fix,
                    )
                    self._transition(TransitionEvent.CONTINUE)

                case State.ACTION_SELECTED:
                    print(
                        "🤖 [ACTION_SELECTED] Invoking local Ollama "
                        "(qwen2.5-coder:7b) to reason over patch payload"
                    )
                    self._raw_llm_output = query_debugger(
                        SYSTEM_PROMPT, self._user_prompt
                    )
                    self._transition(TransitionEvent.CONTINUE)

                case State.ACTED:
                    patch_applied = apply_patch(
                        self.file_path, self._raw_llm_output
                    )
                    if not patch_applied:
                        print(
                            "❌ [ACTED] Patcher failed — invalid or missing "
                            "markdown code block layout"
                        )
                        self._transition(TransitionEvent.HALT)
                    else:
                        print(
                            "✅ [ACTED] Patcher applied fenced code block to "
                            f"{Path(self.file_path).name}"
                        )
                        self.current_retry += 1
                        self._transition(TransitionEvent.CONTINUE)

                case State.TERMINATED:
                    break

        return self._terminated_successfully
