from core.runners.base import AbstractRunner, ExecutionResult
import uuid
import time
import subprocess
import re
import os

class CPPRunner(AbstractRunner):
    def __init__(self, file_path: str):
        self.file_path = file_path

    def execute(self, timeout: int = 5) -> ExecutionResult:
        unique_id = uuid.uuid4().hex
        executable = f"./proc_{unique_id}"
        cmd = ["g++", self.file_path, "-o", executable]
        try:
            try:
                c_res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
                if c_res.returncode != 0:
                    match = re.search(r':(\d+):', c_res.stderr)
                    line_no = int(match.group(1)) if match else None

                    return ExecutionResult(
                        success=False,
                        stage="Compilation",
                        stdout=c_res.stdout,
                        stderr=c_res.stderr,
                        runtime_ms=0.0,
                        exit_code=c_res.returncode,
                        error="Compilation Failed",
                        line_number=line_no
                    )
            except subprocess.TimeoutExpired:
                return ExecutionResult(False, "Compilation", "", "Timeout", 0.0, 124, "Compiler Timed Out")
            except Exception as e:
                return ExecutionResult(False, "System", "", str(e), 0.0, 1, "Internal Script Error")

            os.chmod(executable, 0o755)

            try:
                start = time.time()
                r_res = subprocess.run([executable], capture_output=True, text=True, timeout=timeout)
                end = time.time()
                runtime_ms = (end - start) * 1000

                if r_res.returncode != 0:
                    return ExecutionResult(
                        success=False,
                        stage="Execution",
                        stdout=r_res.stdout,
                        stderr=r_res.stderr,
                        runtime_ms=runtime_ms,
                        exit_code=r_res.returncode,
                        error="Runtime Error"
                    )
                return ExecutionResult(
                    success=True,
                    stage="Execution",
                    stdout=r_res.stdout,
                    stderr=r_res.stderr,
                    runtime_ms=runtime_ms,
                    exit_code=0
                )
            except subprocess.TimeoutExpired:
                return ExecutionResult(False, "Execution", "", "", float(timeout * 1000), 124, "Time Limit Exceeded")
            except Exception as e:
                return ExecutionResult(False, "System", "", str(e), 0.0, 1, "Execution Start Failed")
        finally:
            try:
                os.remove(executable)
            except OSError:
                pass

