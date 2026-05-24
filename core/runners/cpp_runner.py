from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from core.runners.base import AbstractRunner, ExecutionResult
from core.sandbox.docker_engine import DockerSandboxWrapper


class CPPRunner(AbstractRunner):
    _TIMEOUT_EXIT_CODE: int = 124
    _TEMP_EXEC_PATH: str = "/tmp/temp_exec"
    _COMPILE_ERROR_PATTERN = re.compile(r":(\d+):\d*:?\s*error:")

    def __init__(self, file_path: str) -> None:
        self.file_path: str = file_path
        self.filename: str = Path(file_path).name
        self.sandbox: DockerSandboxWrapper = DockerSandboxWrapper()

    def execute(self, timeout: int = 5) -> ExecutionResult:
        temp_exec = self._TEMP_EXEC_PATH
        shell_pipeline = (
            f"g++ -Wall {self.filename} -o {temp_exec} && {temp_exec}"
        )
        command: list[str] = ["/bin/sh", "-c", shell_pipeline]
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
        if success:
            return ExecutionResult(
                success=True,
                stage="Execution",
                stdout=stdout,
                stderr=stderr,
                runtime_ms=runtime_ms,
                exit_code=exit_code,
            )

        if self._is_compilation_failure(stderr):
            return ExecutionResult(
                success=False,
                stage="Compilation",
                stdout=stdout,
                stderr=stderr,
                runtime_ms=runtime_ms,
                exit_code=exit_code,
                error="Compilation Failed",
                line_number=self._extract_compile_line_number(stderr),
            )

        return ExecutionResult(
            success=False,
            stage="Execution",
            stdout=stdout,
            stderr=stderr,
            runtime_ms=runtime_ms,
            exit_code=exit_code,
            error="Runtime Error",
        )

    @classmethod
    def _is_compilation_failure(cls, stderr: str) -> bool:
        return cls._COMPILE_ERROR_PATTERN.search(stderr) is not None

    @staticmethod
    def _extract_compile_line_number(stderr: str) -> Optional[int]:
        match = re.search(r":(\d+):", stderr)
        if match:
            return int(match.group(1))
        return None
