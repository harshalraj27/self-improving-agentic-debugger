from __future__ import annotations

import asyncio
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Final

from fastapi import BackgroundTasks, FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from agent.agent import Agent

SCRATCH_DIR: Final[Path] = Path("data/scratch")
SCRATCH_DIR.mkdir(parents=True, exist_ok=True)

class State(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class Submission(BaseModel):
    code: str = Field(..., description="Raw broken source code content buffer.")
    language: str = Field(..., description="Target execution runtime language ('python' or 'cpp').")
    max_retries: int = Field(5, ge=1, le=10, description="Maximum allocation of execution retry tokens.")

class StatusResponse(BaseModel):
    job_id: str
    state: State
    language: str
    initial_code: str
    fixed_code: str | None = None
    retry_cycles: int = 0
    message: str

_JOB_DB: Dict[str, Dict[str, Any]] = {}