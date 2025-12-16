from enum import Enum
from typing import Any, Dict, Optional
from dataclasses import dataclass

from .job_store import set_job_status, get_job_status


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class JobState:
    job_id: str
    status: JobStatus
    result: Optional[str] = None
    error: Optional[str] = None
    updated_at: Optional[int] = None
    duration_ms: Optional[int] = None


class JobStateStore:
    """Thin wrapper over job_store helpers."""

    def set(self, job_id: str, status: JobStatus, result: Any = None, error: Optional[str] = None, meta: Optional[Dict[str, Any]] = None):
        set_job_status(job_id, status.value, result=result, error=error, meta=meta)

    def get(self, job_id: str) -> Optional[JobState]:
        data = get_job_status(job_id)
        if not data:
            return None
        return JobState(
            job_id=job_id,
            status=JobStatus(data.get("status", JobStatus.QUEUED)),
            result=data.get("result"),
            error=data.get("error"),
            updated_at=int(data.get("updated_at")) if data.get("updated_at") else None,
            duration_ms=int(data.get("duration_ms")) if data.get("duration_ms") else None,
        )


job_state_store = JobStateStore()

