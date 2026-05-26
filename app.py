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

app = FastAPI(
    title="API Gateway",
    version="1.0.0",
    description="Engine for sandboxed code self-correction.",
)

class State(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class Submission(BaseModel):
    code: str = Field(..., description="Raw broken source code.")
    language: str = Field(..., description="Language ('python' or 'cpp').")
    max_retries: int = Field(5, ge=1, le=20, description="Execution retry tokens.")

class StatusResponse(BaseModel):
    job_id: str
    state: State
    language: str
    initial_code: str
    fixed_code: str | None = None
    retry_cycles: int = 0
    message: str

_JOB_DB: Dict[str, Dict[str, Any]] = {}

def _async_background_worker(job_id: str, file_path: Path, max_retries: int) -> None:
    _JOB_DB[job_id]["state"] = State.RUNNING
    _JOB_DB[job_id]["message"] = "Agent initialized. Spinning up isolated compute plane."

    try:
        agent = Agent(file_path=str(file_path), max_retries=max_retries)

        success: bool = agent.run()
        if success:
            _JOB_DB[job_id]["state"] = State.SUCCESS
            _JOB_DB[job_id]["fixed_code"] = file_path.read_text(encoding="utf-8")
            _JOB_DB[job_id]["retry_cycles"] = agent.current_retry
            _JOB_DB[job_id]["message"] = "Source code successfully repaired and validated."
        else:
            _JOB_DB[job_id]["state"] = State.FAILED
            _JOB_DB[job_id]["retry_cycles"] = agent.current_retry
            _JOB_DB[job_id]["message"] = "Agent halted. Spent retry budget or broke structural layouts."

    except Exception as exc:
        _JOB_DB[job_id]["state"] = State.FAILED
        _JOB_DB[job_id]["message"] = f"System execution crash: {str(exc)}"
    finally:
        pass

@app.post(
    "/api/v1/debug/submit",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=Dict[str, str],
    summary="Submit broken code payload for asynchronous self-correction",
)
async def submit_debugging_job(
        payload: Submission,
        background_tasks: BackgroundTasks
) -> Dict[str, str]:
    lang = payload.language.lower().strip()
    if lang not in ("python", "cpp"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language: '{payload.language}'. Supported: ['python', 'cpp']."
        )

    job_id = str(uuid.uuid4())
    extension = "py" if lang == "python" else "cpp"
    job_file_path = SCRATCH_DIR / f"job_{job_id}.{extension}"
    try:
        job_file_path.write_text(payload.code, encoding="utf-8")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to provision isolated scratch disk memory: {str(exc)}"
        )

    _JOB_DB[job_id] = {
        "state": State.PENDING,
        "language": lang,
        "initial_code": payload.code,
        "patched_code": None,
        "retry_cycles_consumed": 0,
        "message": "Job received and queued into background execution threads.",
    }

    background_tasks.add_task(
        _async_background_worker,
        job_id=job_id,
        file_path=job_file_path,
        max_retries=payload.max_retries
    )

    return {"job_id": job_id, "status": "accepted"}

@app.get(
    "/api/v1/debug/status/{job_id}",
    response_model=StatusResponse,
    summary="Poll current lifecycle state and telemetry of a debugging job",
)
async def get_job_status(job_id: str) -> Dict[str, Any]:
    job_record = _JOB_DB.get(job_id)
    if not job_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target debugging job token reference '{job_id}' not found in cluster cache."
        )

    return {
        "job_id": job_id,
        "state": job_record["state"],
        "language": job_record["language"],
        "initial_code": job_record["initial_code"],
        "patched_code": job_record["patched_code"],
        "retry_cycles_consumed": job_record["retry_cycles_consumed"],
        "message": job_record["message"],
    }