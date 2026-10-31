from __future__ import annotations

import asyncio
import json
import logging
import subprocess
import sys
import uuid
from pathlib import Path

from config.settings import get_settings
from data_pipeline.alert_engine import (
    detect_alerts,
    mark_alerts_notified,
    notify_email,
    notify_webhook,
    render_alert_payload,
)
from db.database import isolated_session
from scheduler.celery_app import celery_app


settings = get_settings()
logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _run_scrapy(spider_name: str, *extra_args: str) -> str:
    command = [sys.executable, "-m", "scrapy", "crawl", spider_name, *extra_args]
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-4000:] or result.stdout[-4000:])
    return result.stdout[-4000:]


@celery_app.task(name="scheduler.tasks.run_search_crawl")
def run_search_crawl() -> str:
    return _run_scrapy("search_spider")


async def _collect_asins() -> str:
    from db.crud import get_all_asins

    async with isolated_session() as session:
        asins = await get_all_asins(session)
        return ",".join(record.asin for record in asins)


@celery_app.task(name="scheduler.tasks.run_asin_detail_crawl")
def run_asin_detail_crawl() -> str:
    asin_codes = asyncio.run(_collect_asins())
    if not asin_codes:
        return "No ASINs discovered yet."
    return _run_scrapy("asin_spider", "-a", f"asins={asin_codes}")


@celery_app.task(name="scheduler.tasks.run_seller_offer_crawl")
def run_seller_offer_crawl() -> str:
    asin_codes = asyncio.run(_collect_asins())
    if not asin_codes:
        return "No ASINs discovered yet."
    return _run_scrapy("seller_spider", "-a", f"asins={asin_codes}")


async def _run_alert_check_async() -> list[dict]:
    async with isolated_session() as session:
        alerts = await detect_alerts(session, settings.alert_threshold_pct)
        payload = render_alert_payload(alerts)
        if not alerts:
            return payload
        delivered = False
        try:
            delivered = notify_email("BearingPulse alerts", json.dumps(payload, indent=2))
        except Exception:
            logger.exception("Alert email delivery failed")
        if settings.alert_webhook_url:
            try:
                await notify_webhook(settings.alert_webhook_url, alerts)
                delivered = True
            except Exception:
                logger.exception("Alert webhook delivery failed")
        if delivered:
            await mark_alerts_notified(session, [uuid.UUID(item["alert_id"]) for item in payload])
        return payload


@celery_app.task(name="scheduler.tasks.run_alert_check")
def run_alert_check() -> list[dict]:
    return asyncio.run(_run_alert_check_async())
