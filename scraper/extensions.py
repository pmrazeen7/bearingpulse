from __future__ import annotations

import logging
import os
import time

import redis
from scrapy import signals
from scrapy.exceptions import NotConfigured

from config.settings import get_settings


logger = logging.getLogger(__name__)
PROGRESS_TTL_SECONDS = 24 * 60 * 60


def progress_key(task_id: str) -> str:
    return f"crawl:progress:{task_id}"


class ProgressExtension:
    """Publish crawl progress to Redis so the API/dashboard can show a progress bar.

    Active only when ``CRAWL_TASK_ID`` is set (Celery sets it for each crawl); manual
    ``scrapy crawl`` runs are unaffected. ``done`` counts responses received (retries
    included, so it is capped at ``total``); ``total`` comes from ``spider.expected_total``.
    """

    def __init__(self, task_id: str, client) -> None:
        self.key = progress_key(task_id)
        self.client = client
        self.state = {"done": 0, "items": 0, "total": 0, "finished": 0, "updated": 0}
        self._warned = False

    @classmethod
    def from_crawler(cls, crawler):
        task_id = os.environ.get("CRAWL_TASK_ID")
        if not task_id:
            raise NotConfigured
        client = redis.Redis.from_url(
            get_settings().redis_url, decode_responses=True, socket_connect_timeout=2, socket_timeout=2
        )
        extension = cls(task_id, client)
        crawler.signals.connect(extension.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(extension.response_received, signal=signals.response_received)
        crawler.signals.connect(extension.item_scraped, signal=signals.item_scraped)
        crawler.signals.connect(extension.spider_closed, signal=signals.spider_closed)
        return extension

    def _publish(self) -> None:
        self.state["updated"] = int(time.time())  # lets the API detect a crawl that silently died
        try:
            self.client.hset(self.key, mapping=self.state)
            self.client.expire(self.key, PROGRESS_TTL_SECONDS)
        except Exception as exc:  # progress is best-effort and must never break a crawl
            if not self._warned:
                logger.warning("Could not publish crawl progress: %s", exc)
                self._warned = True

    def spider_opened(self, spider) -> None:
        self.state["total"] = int(getattr(spider, "expected_total", 0) or 0)
        self._publish()

    def response_received(self, response, request, spider) -> None:
        self.state["done"] += 1
        self._publish()

    def item_scraped(self, item, response, spider) -> None:
        self.state["items"] += 1
        self._publish()

    def spider_closed(self, spider, reason) -> None:
        self.state["finished"] = 1
        self._publish()
