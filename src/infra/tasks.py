import time
from typing import Any, Dict, Optional
from uuid import uuid4

from src.services.orchestrator import MasterOrchestrator
from .celery_app import celery_app
from .job_store import set_job_status
from .kafka_events import publish_event_sync
from .state import JobStatus, job_state_store


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True, retry_kwargs={"max_retries": 3})
def run_agentic_job(self, job_id: str, query: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Execute a crew.kickoff asynchronously."""
    start = time.time()
    set_job_status(job_id, status="running", meta={"started_at": int(start * 1000)})

    try:
        orchestrator = MasterOrchestrator()
        result_obj = orchestrator.process_query(query, context)
        result = result_obj.content
        duration_ms = int((time.time() - start) * 1000)

        set_job_status(
            job_id,
            status="done",
            result=str(result),
            meta={"finished_at": int(time.time() * 1000), "duration_ms": duration_ms},
        )

        publish_event_sync(
            "agent.completed",
            {"job_id": job_id, "status": "done", "duration_ms": duration_ms, "summary": str(result)[:500]},
        )
        return str(result)

    except Exception as exc:
        set_job_status(job_id, status="failed", error=str(exc), meta={"finished_at": int(time.time() * 1000)})
        publish_event_sync(
            "agent.completed",
            {"job_id": job_id, "status": "failed", "error": str(exc)},
        )
        raise


def submit_job(query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Queue a job and return its id and initial state."""
    job_id = uuid4().hex
    job_state_store.set(job_id, JobStatus.QUEUED, meta={"submitted_at": int(time.time() * 1000)})
    run_agentic_job.delay(job_id=job_id, query=query, context=context)
    return {"job_id": job_id, "status": JobStatus.QUEUED}

