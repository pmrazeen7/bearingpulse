from __future__ import annotations

import logging
import time
from typing import Literal

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.concurrency import run_in_threadpool


router = APIRouter(prefix="/crawl", tags=["crawl"])
logger = logging.getLogger(__name__)

JOBS = {
    "search": "scheduler.tasks.run_search_crawl",
    "asin-detail": "scheduler.tasks.run_asin_detail_crawl",
    "seller-offers": "scheduler.tasks.run_seller_offer_crawl",
    "alert-check": "scheduler.tasks.run_alert_check",
}
# No progress update for this long while "running" means the worker or crawler is gone
# (for example the container was restarted mid-crawl). Requests are seconds apart, so this is generous.
STALL_AFTER_SECONDS = 300
QUEUE_DOWN = "Task queue (Redis/Celery) is unavailable. Start Redis and a Celery worker, then retry."
Job = Literal["search", "asin-detail", "seller-offers", "alert-check"]


def _send(task_name: str) -> str:
    from scheduler.celery_app import celery_app

    return celery_app.send_task(task_name, retry=False).id


def _celery_state(task_id: str) -> dict:
    from scheduler.celery_app import celery_app

    result = celery_app.AsyncResult(task_id)
    payload = {"state": result.state}
    if result.failed():
        payload["error"] = str(result.result)[-600:]
    elif result.successful() and isinstance(result.result, str):
        payload["summary"] = result.result[-300:]
    return payload


def summarize(celery: dict, progress: dict, now: float | None = None) -> dict:
    """Combine Celery's task state with the crawler's live counters into one payload."""
    state = celery["state"]
    done, total = int(progress.get("done", 0)), int(progress.get("total", 0))
    items = int(progress.get("items", 0))
    if state == "PENDING" and done > 0:
        state = "STARTED"  # live counters prove it is running even if Celery has not recorded the start
    if state == "SUCCESS":
        percent: int | None = 100
    elif state in {"STARTED", "PROGRESS", "RETRY"} and total > 0:
        percent = min(99, int(done * 100 / total))
    else:
        percent = None  # queued, or running without a known total: show an indeterminate bar
    status = {
        "SUCCESS": "success",
        "FAILURE": "failed",
        "REVOKED": "failed",
        "PENDING": "queued",
    }.get(state, "running")
    idle = None
    updated = int(progress.get("updated", 0) or 0)
    if status == "running" and updated:
        idle = max(0, int((now if now is not None else time.time()) - updated))
        if idle > STALL_AFTER_SECONDS:
            status = "stalled"
    return {
        "status": status,
        "idle_seconds": idle,
        "celery_state": state,
        "percent": percent,
        "done": min(done, total) if total else done,
        "total": total or None,
        "items": items,
        **{key: celery[key] for key in ("error", "summary") if key in celery},
    }


@router.get("/jobs")
async def list_jobs():
    return [{"job": job, "task": task} for job, task in JOBS.items()]


@router.post("/{job}", status_code=status.HTTP_202_ACCEPTED)
async def trigger_job(job: Job, request: Request):
    # Celery's Redis backend retries ~20 times before failing, which would hang this
    # request. Probe Redis with the app's short-timeout client first.
    try:
        await request.app.state.redis.ping()
    except Exception as exc:
        logger.warning("Redis unreachable, not enqueuing %s: %s", job, exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=QUEUE_DOWN) from exc
    try:
        task_id = await run_in_threadpool(_send, JOBS[job])
    except Exception as exc:  # broker unreachable: report it instead of hanging the request
        logger.warning("Could not enqueue %s: %s", job, exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=QUEUE_DOWN) from exc
    return {"status": "queued", "job": job, "task_id": task_id}


@router.get("/tasks/{task_id}")
async def task_status(task_id: str, request: Request):
    try:
        celery = await run_in_threadpool(_celery_state, task_id)
        progress = await request.app.state.redis.hgetall(f"crawl:progress:{task_id}")
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Task result backend is unavailable") from exc
    return {"task_id": task_id, **summarize(celery, progress or {})}
