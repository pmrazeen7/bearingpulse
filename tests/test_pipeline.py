import pytest
from pydantic import ValidationError
from scrapy.exceptions import DropItem

from anti_bot.proxy_manager import ProxyManager, redact_proxy
from config.settings import Settings
from scraper.pipelines import DatabasePipeline


def test_redact_proxy_hides_credentials():
    assert redact_proxy("http://scrapeops:secret-key@proxy.scrapeops.io:5353") == "http://***@proxy.scrapeops.io:5353"
    assert redact_proxy("http://10.0.0.1:8080") == "http://10.0.0.1:8080"
    assert redact_proxy(None) is None


def test_proxy_manager_retires_unhealthy_proxies():
    manager = ProxyManager(local_proxies=["http://a:1", "http://b:2"])
    manager.settings = manager.settings.model_copy(update={"scrapeops_api_key": ""})
    for _ in range(5):
        manager.record_failure("http://a:1")
    manager.retire_unhealthy()
    assert manager.get_proxy() == "http://b:2"


def test_database_url_normalisation():
    from db.database import normalize_async_url, normalize_sync_url

    url = "postgresql://u:p@postgres:5432/db"
    assert normalize_async_url(url) == "postgresql+asyncpg://u:p@postgres:5432/db"
    assert normalize_sync_url(url) == "postgresql+psycopg2://u:p@postgres:5432/db"
    assert normalize_sync_url("postgresql+asyncpg://u:p@h/db") == "postgresql+psycopg2://u:p@h/db"
    assert normalize_sync_url("sqlite+aiosqlite:///x.db") == "sqlite:///x.db"


def test_settings_parse_comma_separated_lists():
    settings = Settings(cors_origins="http://a.test, http://b.test", search_queries="SKF 6205,SKF 6206", _env_file=None)
    assert settings.cors_origins == ["http://a.test", "http://b.test"]
    assert settings.search_queries == ["SKF 6205", "SKF 6206"]


def test_production_rejects_default_api_key():
    with pytest.raises(ValidationError):
        Settings(app_env="production", api_key="change-me", _env_file=None)
    assert Settings(app_env="production", api_key="a-long-random-secret", _env_file=None).is_production


@pytest.mark.asyncio
async def test_pipeline_drops_items_without_price():
    pipeline = DatabasePipeline()
    with pytest.raises(DropItem):
        await pipeline.process_item({"source": "product", "asin": "B012345678", "current_price": None}, None)
    with pytest.raises(DropItem):
        await pipeline.process_item({"source": "search", "asin": "short"}, None)
    with pytest.raises(DropItem):
        await pipeline.process_item({"source": "mystery"}, None)
