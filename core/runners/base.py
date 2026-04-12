from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class ExecutionResult:
    success: bool
    stage: str
    stdout: str
    stderr: str
    runtime_ms: float
    exit_code: int
    error: Optional[str] = None
    line_number: Optional[int] = None

class AbstractRunner(ABC):
    @abstractmethod
    def execute(file_path)->ExecutionResult:
        pass