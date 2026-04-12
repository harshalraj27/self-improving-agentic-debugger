from typing import Optional
from base import AbstractRunner, ExecutionResult
import subprocess
import sys
import time
import re

class PyRunner(AbstractRunner):
    def __init__(self, file_path: str):
        self.file_path = file_path

    def execute(self, timeout: int = 5) -> ExecutionResult:
        start = time.time()
        try:
            result = subprocess.run(
                [sys.executable, self.file_path],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            success = (result.returncode == 0)
            trace = result.stderr if not success else ""

            err_type = self._extract_error_type(trace)
            err_msg = self._extract_error_message(trace)
            line_number = self._extract_line_number(trace)
            return ExecutionResult(
                success=success,
                stage="execution",
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                line_number=line_number,
                runtime_ms=(time.time() - start) * 1000,
                error=f"{err_type}: {err_msg}" if err_type else None
            )

        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                stage="timeout",
                exit_code=-1,
                stdout="",
                stderr="Timeout reached",
                runtime_ms=timeout * 1000,
                error="TimeoutError"
            )

    def _extract_error_type(self, traceback_str: str):
        if not traceback_str:
            return None
        lines = traceback_str.strip().splitlines()
        if lines:
            last = lines[-1]
            if ":" in last:
                return last.split(":")[0]
        return None

    def _extract_error_message(self, traceback_str: str):
        if not traceback_str:
            return None
        lines = traceback_str.strip().splitlines()
        if lines:
            last = lines[-1]
            if ":" in last:
                return last.split(":", 1)[1].strip()
        return None

    def _extract_line_number(self, traceback_str: str) -> Optional[int]:
        if not traceback_str:
            return None
        matches = re.findall(r'line (\d+)', traceback_str)
        if matches:
            return int(matches[-1])
        return None