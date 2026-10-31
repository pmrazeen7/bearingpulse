from __future__ import annotations

import logging
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
QUEUE_DOWN = "Task queue (Redis/Celery) is unavailable. Start Redis and a Celery worker, then retry."
Job = Literal["search", "asin-detail", "seller-offers", "alert-check"]


def _send(task_name: str) -> str:
    from scheduler.celery_app import celery_app

    return celery_app.send_task(task_name, retry=False).id


def _state(task_id: str) -> dict:
    from scheduler.celery_app import celery_app

    result = celery_app.AsyncResult(task_id)
    payload = {"task_id": task_id, "state": result.state}
    if result.failed():
        payload["error"] = str(result.result)
    return payload


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
async def task_status(task_id: str):
    try:
        return await run_in_threadpool(_state, task_id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Task result backend is unavailable") from exc
