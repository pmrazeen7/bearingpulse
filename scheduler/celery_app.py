from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from config.settings import get_settings


settings = get_settings()
celery_app = Celery("price_monitor", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    timezone="Asia/Kolkata",
    imports=("scheduler.tasks",),
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=60 * 60 * 24,
    broker_connection_retry_on_startup=True,
    # Keep API-side enqueues from hanging when Redis is down.
    broker_transport_options={"socket_connect_timeout": 3, "socket_timeout": 5},
    redis_socket_connect_timeout=3,
    beat_schedule={
        "run-search-crawl": {
            "task": "scheduler.tasks.run_search_crawl",
            "schedule": crontab(minute=0, hour="*/6"),
        },
        "run-asin-detail-crawl": {
            "task": "scheduler.tasks.run_asin_detail_crawl",
            "schedule": crontab(minute=0, hour="*/2"),
        },
        "run-seller-offer-crawl": {
            "task": "scheduler.tasks.run_seller_offer_crawl",
            "schedule": crontab(minute="*/30"),
        },
        "run-alert-check": {
            "task": "scheduler.tasks.run_alert_check",
            "schedule": crontab(minute="*/15"),
        },
    },
)

