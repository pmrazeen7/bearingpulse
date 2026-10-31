from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import api.main as api_main
import api.routes.crawl as crawl_routes
from api.main import app
from db import crud
from db.database import get_db_session


AUTH = {"X-API-Key": "test-key"}


class DummyRedis:
    def __init__(self, healthy: bool = True):
        self.healthy = healthy

    async def ping(self):
        if not self.healthy:
            raise ConnectionError("redis down")
        return True

    def close(self):
        return None


@pytest_asyncio.fixture
async def client(session_factory) -> AsyncIterator[AsyncClient]:
    async def override_get_db_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.state.redis = DummyRedis()
    api_main.settings.api_key = "test-key"

    now = datetime.now(UTC)
    async with session_factory() as session:
        await crud.create_price_snapshot(
            session,
            asin="B012345678",
            seller_name="Seller API",
            price=999.0,
            mrp=1200.0,
            is_buy_box_winner=True,
            stock_status="in_stock",
            scraped_at=now - timedelta(hours=2),
        )
        await crud.create_price_snapshot(
            session,
            asin="B012345678",
            seller_name="Rival Bearings",
            price=899.0,
            is_buy_box_winner=True,
            stock_status="in_stock",
            scraped_at=now - timedelta(hours=1),
        )
        await crud.upsert_asin(session, asin="B099999999", title="SKF 6300 Deep Groove")
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_is_public_and_reports_components(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "ok", "redis": "ok", "version": app.version}


@pytest.mark.asyncio
async def test_health_degrades_when_redis_is_down(client: AsyncClient):
    app.state.redis = DummyRedis(healthy=False)
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["redis"] == "unavailable"


@pytest.mark.asyncio
async def test_protected_routes_require_api_key(client: AsyncClient):
    assert (await client.get("/api/asins")).status_code == 401
    assert (await client.get("/api/asins", headers={"X-API-Key": "wrong"})).status_code == 401
    assert (await client.get("/api/auth/verify", headers=AUTH)).status_code == 200


@pytest.mark.asyncio
async def test_list_asins_includes_latest_snapshot_once(client: AsyncClient):
    response = await client.get("/api/asins", headers=AUTH)
    assert response.status_code == 200
    assert response.headers["X-Total-Count"] == "2"
    rows = {row["asin"]: row for row in response.json()}
    assert len(response.json()) == 2
    assert rows["B012345678"]["latest_price"] == 899.0
    assert rows["B012345678"]["latest_seller"] == "Rival Bearings"
    assert rows["B012345678"]["seller_count"] == 2
    assert rows["B099999999"]["latest_price"] is None


@pytest.mark.asyncio
async def test_asin_search_and_pagination(client: AsyncClient):
    response = await client.get("/api/asins?q=6300", headers=AUTH)
    assert [row["asin"] for row in response.json()] == ["B099999999"]
    assert response.headers["X-Total-Count"] == "1"

    page = await client.get("/api/asins?limit=1&offset=1", headers=AUTH)
    assert len(page.json()) == 1
    assert page.headers["X-Total-Count"] == "2"


@pytest.mark.asyncio
async def test_asin_detail_reports_buybox_change(client: AsyncClient):
    response = await client.get("/api/asins/b012345678", headers=AUTH)
    assert response.status_code == 200
    detail = response.json()
    assert detail["snapshot_count"] == 2
    assert detail["buy_box_seller"] == "Rival Bearings"
    assert detail["buy_box_change_pct"] == pytest.approx(-10.01, abs=0.01)
    assert (await client.get("/api/asins/B000000000", headers=AUTH)).status_code == 404


@pytest.mark.asyncio
async def test_track_and_untrack_asin(client: AsyncClient):
    created = await client.post("/api/asins", headers=AUTH, json={"asin": "b0abcdef12", "title": "SKF 6207"})
    assert created.status_code == 201
    assert created.json()["asin"] == "B0ABCDEF12"

    duplicate = await client.post("/api/asins", headers=AUTH, json={"asin": "B0ABCDEF12"})
    assert duplicate.status_code == 409

    invalid = await client.post("/api/asins", headers=AUTH, json={"asin": "nope"})
    assert invalid.status_code == 422

    assert (await client.delete("/api/asins/B012345678", headers=AUTH)).status_code == 204
    assert (await client.get("/api/asins/B012345678", headers=AUTH)).status_code == 404
    assert (await client.delete("/api/asins/B012345678", headers=AUTH)).status_code == 404


@pytest.mark.asyncio
async def test_asin_prices_endpoint(client: AsyncClient):
    response = await client.get("/api/asins/B012345678/prices?days=7", headers=AUTH)
    assert response.status_code == 200
    assert [row["seller_name"] for row in response.json()] == ["Seller API", "Rival Bearings"]


@pytest.mark.asyncio
async def test_invalid_days_rejected(client: AsyncClient):
    response = await client.get("/api/asins/B012345678/prices?days=15", headers=AUTH)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_asin_sellers_returns_latest_offer_per_seller(client: AsyncClient):
    response = await client.get("/api/asins/B012345678/sellers", headers=AUTH)
    assert [row["current_price"] for row in response.json()] == [899.0, 999.0]


@pytest.mark.asyncio
async def test_sellers_listing_detail_and_invalid_id(client: AsyncClient):
    listing = await client.get("/api/sellers?q=rival", headers=AUTH)
    assert listing.headers["X-Total-Count"] == "1"
    seller = listing.json()[0]
    assert seller["buy_box_wins"] == 1

    detail = await client.get(f"/api/sellers/{seller['seller_id']}", headers=AUTH)
    assert detail.json()["seller_name"] == "Rival Bearings"

    asins = await client.get(f"/api/sellers/{seller['seller_id']}/asins", headers=AUTH)
    assert asins.json()[0]["asin"] == "B012345678"

    assert (await client.get("/api/sellers/not-a-uuid/asins", headers=AUTH)).status_code == 404


@pytest.mark.asyncio
async def test_overview_counts_real_rows(client: AsyncClient):
    response = await client.get("/api/analytics/overview", headers=AUTH)
    body = response.json()
    assert body["asin_count"] == 2
    assert body["seller_count"] == 2
    assert body["snapshot_count"] == 2
    assert len(body["activity"]) == 14
    assert sum(day["snapshots"] for day in body["activity"]) == 2


@pytest.mark.asyncio
async def test_alert_check_acknowledge_and_export(client: AsyncClient):
    check = await client.post("/api/alerts/check", headers=AUTH)
    assert check.status_code == 200
    created_types = {alert["alert_type"] for alert in check.json()["alerts"]}
    assert created_types == {"price_drop", "buybox_change"}

    rerun = await client.post("/api/alerts/check", headers=AUTH)
    assert rerun.json()["created"] == 0

    listing = await client.get("/api/alerts?type=price_drop", headers=AUTH)
    assert listing.headers["X-Total-Count"] == "1"
    alert_id = listing.json()[0]["id"]

    patched = await client.patch(f"/api/alerts/{alert_id}", headers=AUTH, json={"acknowledged": True})
    assert patched.json()["acknowledged"] is True
    open_alerts = await client.get("/api/alerts?acknowledged=false", headers=AUTH)
    assert open_alerts.headers["X-Total-Count"] == "1"

    bulk = await client.post("/api/alerts/acknowledge-all", headers=AUTH)
    assert bulk.json()["updated"] == 1

    export = await client.get("/api/alerts/export.csv", headers=AUTH)
    assert export.status_code == 200
    assert export.headers["content-type"].startswith("text/csv")
    assert "attachment" in export.headers["content-disposition"]
    assert export.text.splitlines()[0].startswith("id,asin,title,alert_type")
    assert len(export.text.strip().splitlines()) == 3

    assert (await client.patch("/api/alerts/bad-id", headers=AUTH, json={})).status_code == 404


@pytest.mark.asyncio
async def test_alert_config_is_persisted_and_used(client: AsyncClient):
    response = await client.post(
        "/api/alerts/config",
        headers=AUTH,
        json={"threshold_pct": 50, "asin_id": "b012345678"},
    )
    assert response.status_code == 200
    assert response.json()["config"]["threshold_pct"] == 50

    configs = (await client.get("/api/alerts/config", headers=AUTH)).json()
    assert {config["scope"] for config in configs} == {"default", "B012345678"}

    # A 10% drop no longer crosses the 50% override.
    check = await client.post("/api/alerts/check", headers=AUTH)
    assert "price_drop" not in {alert["alert_type"] for alert in check.json()["alerts"]}

    unknown = await client.post("/api/alerts/config", headers=AUTH, json={"threshold_pct": 5, "asin_id": "B000000001"})
    assert unknown.status_code == 404
    bad = await client.post("/api/alerts/config", headers=AUTH, json={"threshold_pct": 5, "asin_id": "asin-123"})
    assert bad.status_code == 422

    assert (await client.delete("/api/alerts/config/B012345678", headers=AUTH)).status_code == 204
    assert (await client.delete("/api/alerts/config/default", headers=AUTH)).status_code == 400


@pytest.mark.asyncio
async def test_crawl_trigger_reports_unavailable_queue(client: AsyncClient, monkeypatch):
    def broken_send(_task_name):
        raise ConnectionError("redis down")

    monkeypatch.setattr(crawl_routes, "_send", broken_send)
    response = await client.post("/api/crawl/search", headers=AUTH)
    assert response.status_code == 503

    app.state.redis = DummyRedis(healthy=False)
    assert (await client.post("/api/crawl/search", headers=AUTH)).status_code == 503

    app.state.redis = DummyRedis()
    monkeypatch.setattr(crawl_routes, "_send", lambda _task_name: "task-123")
    queued = await client.post("/api/crawl/search", headers=AUTH)
    assert queued.status_code == 202
    assert queued.json()["task_id"] == "task-123"

    assert (await client.post("/api/crawl/unknown", headers=AUTH)).status_code == 422


@pytest.mark.asyncio
async def test_cors_allows_react_frontend(client: AsyncClient):
    response = await client.options(
        "/api/asins",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-API-Key",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
