from typing import Any, Dict, Optional
import time

_memory_store: Dict[str, Dict[str, Any]] = {}


def _now_ms() -> int:
    return int(time.time() * 1000)


def _job_key(job_id: str) -> str:
    return f"jobs:{job_id}"


def set_job_status(job_id: str, status: str, result: Any = None, error: Optional[str] = None, meta: Optional[Dict[str, Any]] = None) -> None:
    payload: Dict[str, Any] = {"status": status, "updated_at": _now_ms()}
    if result is not None:
        payload["result"] = result
    if error:
        payload["error"] = error
    if meta:
        payload.update(meta)
    existing = _memory_store.get(job_id, {})
    existing.update(payload)
    _memory_store[job_id] = existing


def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    return _memory_store.get(job_id)

