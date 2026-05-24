from __future__ import annotations

from pathlib import Path

from agent import states
from agent.llm_agent import query_debugger
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
        self._user_prompt: str = ""
        self._raw_llm_output: str = ""
        self._terminated_successfully: bool = False

    def _transition(self, event: TransitionEvent) -> None:
        self.state = states.validate_and_get_next(self.state, event)

    def run(self) -> bool:
        while self.state is not State.TERMINATED:
            match self.state:
                case State.READY:
                    runner = RunnerFactory.get_runner(self.file_path)
                    self.last_run_result = runner.execute()
                    self._transition(TransitionEvent.CONTINUE)

                case State.OBSERVED:
                    if self.last_run_result is None:
                        self._transition(TransitionEvent.HALT)
                        continue
                    if self.last_run_result.success:
                        self._terminated_successfully = True
                        self._transition(TransitionEvent.SUCCESS)
                    elif self.current_retry >= self.max_retries:
                        self._transition(TransitionEvent.HALT)
                    else:
                        self._transition(TransitionEvent.CONTINUE)

                case State.EVALUATED:
                    source_code = Path(self.file_path).read_text(encoding="utf-8")
                    if self.last_run_result is None:
                        self._transition(TransitionEvent.HALT)
                        continue
                    self._user_prompt = generate_user_prompt(
                        source_code, self.last_run_result
                    )
                    self._transition(TransitionEvent.CONTINUE)

                case State.ACTION_SELECTED:
                    self._raw_llm_output = query_debugger(
                        SYSTEM_PROMPT, self._user_prompt
                    )
                    self._transition(TransitionEvent.CONTINUE)

                case State.ACTED:
                    if not apply_patch(self.file_path, self._raw_llm_output):
                        self._transition(TransitionEvent.HALT)
                    else:
                        self.current_retry += 1
                        self._transition(TransitionEvent.CONTINUE)

                case State.TERMINATED:
                    break

        return self._terminated_successfully
