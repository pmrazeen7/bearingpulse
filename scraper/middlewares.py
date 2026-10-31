from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from scrapy import Request
from scrapy.exceptions import IgnoreRequest

from anti_bot.geo_simulator import build_geo_session
from anti_bot.proxy_manager import proxy_manager, redact_proxy
from anti_bot.useragent_pool import get_random_user_agent
from config.settings import get_settings


settings = get_settings()
logger = logging.getLogger(__name__)
MAX_BLOCK_RETRIES = 3


def _write_json_log(payload: dict) -> None:
    payload["timestamp"] = datetime.now(UTC).isoformat()
    with settings.json_log_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, default=str) + "\n")


class RandomUserAgentMiddleware:
    def process_request(self, request: Request, spider=None):
        request.headers["User-Agent"] = get_random_user_agent()
        geo_config = build_geo_session(request.meta.get("pincode"))
        request.headers["X-Forwarded-For"] = geo_config.headers["X-Forwarded-For"]
        request.headers["Accept-Language"] = geo_config.headers["Accept-Language"]
        for key, value in geo_config.cookies.items():
            request.cookies[key] = value
        request.meta["simulated_pincode"] = geo_config.pincode


class ProxyRotationMiddleware:
    def process_request(self, request: Request, spider=None):
        proxy = proxy_manager.get_proxy(request.url, request.meta.get("retry_times", 0))
        if proxy:
            request.meta["proxy"] = proxy
            request.meta["proxy_key"] = proxy
        _write_json_log(
            {"event": "scrape_attempt", "url": request.url, "proxy": redact_proxy(proxy), "spider": _name(spider)}
        )

    def process_response(self, request: Request, response, spider=None):
        if response.status < 400:
            proxy_manager.record_success(request.meta.get("proxy_key"))
            _write_json_log(
                {"event": "scrape_success", "url": request.url, "status": response.status, "spider": _name(spider)}
            )
        return response

    def process_exception(self, request: Request, exception, spider=None):
        proxy_manager.record_failure(request.meta.get("proxy_key"))
        proxy_manager.retire_unhealthy()
        _write_json_log(
            {"event": "scrape_failure", "url": request.url, "error": str(exception), "spider": _name(spider)}
        )


class BlockedResponseRetryMiddleware:
    """Re-queue 403/429/503 responses on a fresh proxy and user agent.

    Backoff is left to AutoThrottle (see ``scraper/settings.py``); sleeping here
    would block the Twisted reactor and stall every in-flight request.
    """

    RETRY_HTTP_CODES = {403, 429, 503}

    def process_response(self, request, response, spider=None):
        if response.status not in self.RETRY_HTTP_CODES:
            return response
        attempt = request.meta.get("retry_times", 0) + 1
        proxy_manager.record_failure(request.meta.get("proxy_key"))
        proxy_manager.retire_unhealthy()
        if attempt > MAX_BLOCK_RETRIES:
            _write_json_log({"event": "scrape_blocked", "url": request.url, "status": response.status})
            raise IgnoreRequest(f"Retry limit reached for {request.url}")
        new_request = request.replace(dont_filter=True, priority=request.priority - attempt)
        new_request.meta["retry_times"] = attempt
        return new_request


# Backwards-compatible alias for older settings files.
ExponentialBackoffRetryMiddleware = BlockedResponseRetryMiddleware


def _name(spider) -> str | None:
    return getattr(spider, "name", None)
