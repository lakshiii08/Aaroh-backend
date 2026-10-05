import uuid
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable
from app.core.logging import logger

class TaskRegistry:
    """In-memory async task tracking for long-running operations."""
    _tasks: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register_task(cls, task_type: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        cls._tasks[job_id] = {
            "job_id": job_id,
            "task_type": task_type,
            "status": "processing",
            "progress_pct": 0,
            "result": None,
            "error": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        }
        return job_id

    @classmethod
    def update_progress(cls, job_id: str, progress_pct: int, status: str = "processing"):
        if job_id in cls._tasks:
            cls._tasks[job_id]["progress_pct"] = progress_pct
            cls._tasks[job_id]["status"] = status
            cls._tasks[job_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

    @classmethod
    def complete_task(cls, job_id: str, result: Any):
        if job_id in cls._tasks:
            cls._tasks[job_id]["status"] = "completed"
            cls._tasks[job_id]["progress_pct"] = 100
            cls._tasks[job_id]["result"] = result
            cls._tasks[job_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

    @classmethod
    def fail_task(cls, job_id: str, error_message: str):
        if job_id in cls._tasks:
            cls._tasks[job_id]["status"] = "failed"
            cls._tasks[job_id]["error"] = error_message
            cls._tasks[job_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

    @classmethod
    def get_task(cls, job_id: str) -> Optional[Dict[str, Any]]:
        return cls._tasks.get(job_id)

async def run_async_job(job_id: str, async_func: Callable, *args, **kwargs):
    """Executes a long running task and registers completion or failure."""
    try:
        logger.info(f"Starting background job: {job_id}")
        TaskRegistry.update_progress(job_id, 10, "processing")
        result = await async_func(*args, **kwargs) if asyncio.iscoroutinefunction(async_func) else async_func(*args, **kwargs)
        TaskRegistry.complete_task(job_id, result)
        logger.info(f"Completed background job: {job_id}")
    except Exception as e:
        logger.error(f"Failed background job {job_id}: {e}", exc_info=True)
        TaskRegistry.fail_task(job_id, str(e))
