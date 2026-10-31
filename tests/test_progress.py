import pytest
from scrapy.exceptions import NotConfigured

import api.routes.crawl as crawl_routes
from api.main import app
from api.routes.crawl import summarize
from scraper.extensions import ProgressExtension, progress_key
from scraper.spiders.asin_spider import AsinSpider
from scraper.spiders.search_spider import SearchSpider
from scraper.spiders.seller_spider import SellerSpider
from tests.test_api import AUTH, DummyRedis, client  # noqa: F401


class FakeRedis:
    def __init__(self):
        self.hashes, self.ttl = {}, {}

    def hset(self, key, mapping):
        self.hashes.setdefault(key, {}).update({k: str(v) for k, v in mapping.items()})

    def expire(self, key, seconds):
        self.ttl[key] = seconds


class BrokenRedis:
    def hset(self, *args, **kwargs):
        raise ConnectionError("down")

    def expire(self, *args, **kwargs):
        raise ConnectionError("down")


def test_spiders_report_expected_totals():
    assert AsinSpider(asins="B012345678,B012345679").expected_total == 2
    assert SellerSpider(asins="B012345678").expected_total == 9
    assert SearchSpider().expected_total == 30


def test_extension_publishes_counters_to_redis():
    fake = FakeRedis()
    ext = ProgressExtension("task-1", fake)
    ext.spider_opened(AsinSpider(asins="B012345678,B012345679,B012345680"))
    ext.response_received(None, None, None)
    ext.item_scraped(None, None, None)
    ext.response_received(None, None, None)
    ext.spider_closed(None, "finished")
    data = fake.hashes[progress_key("task-1")]
    assert data == {"done": "2", "items": "1", "total": "3", "finished": "1"}
    assert fake.ttl[progress_key("task-1")] > 0


def test_extension_never_breaks_a_crawl_when_redis_is_down():
    ext = ProgressExtension("task-2", BrokenRedis())
    ext.response_received(None, None, None)  # must not raise
    ext.response_received(None, None, None)
    assert ext.state["done"] == 2


def test_extension_is_inactive_without_task_id(monkeypatch):
    monkeypatch.delenv("CRAWL_TASK_ID", raising=False)
    with pytest.raises(NotConfigured):
        ProgressExtension.from_crawler(object())


def test_summarize_progress_math():
    running = summarize({"state": "STARTED"}, {"done": "9", "total": "30", "items": "4"})
    assert (running["status"], running["percent"], running["done"], running["total"]) == ("running", 30, 9, 30)
    # Retries can push `done` past `total`; never show 100% until Celery says it's finished.
    over = summarize({"state": "STARTED"}, {"done": "35", "total": "30"})
    assert over["percent"] == 99 and over["done"] == 30
    assert summarize({"state": "PENDING"}, {})["status"] == "queued"
    assert summarize({"state": "PENDING"}, {"done": "2", "total": "4"})["status"] == "running"
    assert summarize({"state": "STARTED"}, {})["percent"] is None
    assert summarize({"state": "SUCCESS"}, {"done": "3", "total": "3"})["percent"] == 100
    failed = summarize({"state": "FAILURE", "error": "boom"}, {})
    assert failed["status"] == "failed" and failed["error"] == "boom"


@pytest.mark.asyncio
async def test_task_status_endpoint_merges_celery_and_progress(client, monkeypatch):  # noqa: F811
    class ProgressRedis(DummyRedis):
        async def hgetall(self, key):
            assert key == "crawl:progress:abc"
            return {"done": "5", "total": "10", "items": "2"}

    app.state.redis = ProgressRedis()
    monkeypatch.setattr(crawl_routes, "_celery_state", lambda _id: {"state": "STARTED"})
    response = await client.get("/api/crawl/tasks/abc", headers=AUTH)
    assert response.status_code == 200
    assert response.json() == {
        "task_id": "abc", "status": "running", "celery_state": "STARTED",
        "percent": 50, "done": 5, "total": 10, "items": 2,
    }

    def broken(_id):
        raise ConnectionError("redis down")

    monkeypatch.setattr(crawl_routes, "_celery_state", broken)
    assert (await client.get("/api/crawl/tasks/abc", headers=AUTH)).status_code == 503
