from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from core.runners.base import AbstractRunner, ExecutionResult
from core.sandbox.docker_engine import DockerSandboxWrapper


class PyRunner(AbstractRunner):
    _TIMEOUT_EXIT_CODE: int = 124

    def __init__(self, file_path: str) -> None:
        self.file_path: str = file_path
        self.filename: str = Path(file_path).name
        self.sandbox: DockerSandboxWrapper = DockerSandboxWrapper()

    def execute(self, timeout: int = 5) -> ExecutionResult:
        command: list[str] = ["python3", self.filename]
        exit_code, stdout, stderr, runtime_ms = self.sandbox.run_in_container(
            self.file_path,
            command,
            timeout,
        )

        if exit_code == self._TIMEOUT_EXIT_CODE:
            return ExecutionResult(
                success=False,
                stage="timeout",
                stdout=stdout,
                stderr=stderr,
                runtime_ms=runtime_ms,
                exit_code=exit_code,
                error="TimeoutError",
            )

        success = exit_code == 0
        trace = stderr if not success else ""
        stage = self._resolve_stage(trace)
        err_type = self._extract_error_type(trace)
        err_msg = self._extract_error_message(trace)
        line_number = self._extract_line_number(trace)

        return ExecutionResult(
            success=success,
            stage=stage,
            stdout=stdout,
            stderr=stderr,
            runtime_ms=runtime_ms,
            exit_code=exit_code,
            line_number=line_number,
            error=f"{err_type}: {err_msg}" if err_type else None,
        )

    @staticmethod
    def _resolve_stage(traceback_str: str) -> str:
        if "SyntaxError" in traceback_str:
            return "Compilation"
        return "Execution"

    @staticmethod
    def _extract_error_type(traceback_str: str) -> Optional[str]:
        if not traceback_str:
            return None
        lines = traceback_str.strip().splitlines()
        if lines:
            last = lines[-1]
            if ":" in last:
                return last.split(":")[0].strip()
        return None

    @staticmethod
    def _extract_error_message(traceback_str: str) -> Optional[str]:
        if not traceback_str:
            return None
        lines = traceback_str.strip().splitlines()
        if lines:
            last = lines[-1]
            if ":" in last:
                return last.split(":", 1)[1].strip()
        return None

    @staticmethod
    def _extract_line_number(traceback_str: str) -> Optional[int]:
        if not traceback_str:
            return None
        matches = re.findall(r"line (\d+)", traceback_str)
        if matches:
            return int(matches[-1])
        return None
