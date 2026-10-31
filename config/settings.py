from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, List

from pydantic import Field, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent
INSECURE_API_KEYS = {"", "change-me", "your_dashboard_api_key_here"}


def _split_csv(value: object) -> object:
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "BearingPulse Price Monitor"
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://user:password@postgres:5432/pricedb"
    redis_url: str = "redis://redis:6379/0"
    scrapeops_api_key: str = ""
    proxy_list: str = ""
    api_key: str = "change-me"
    alert_threshold_pct: float = 5.0
    alert_email: str = "notify@example.com"
    alert_webhook_url: str = ""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    scrape_interval_minutes: int = 30
    max_concurrent_requests: int = 8
    download_delay: float = 2.0
    cors_origins: Annotated[List[str], NoDecode] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://localhost:8501",
            "http://127.0.0.1:8501",
        ]
    )
    json_log_file: Path = BASE_DIR / "logs" / "scraper.jsonl"
    dashboard_api_base: str = "http://app:8000/api"
    playwright_timeout_ms: int = 30000
    search_queries: Annotated[List[str], NoDecode] = Field(
        default_factory=lambda: [
            "SKF 6205",
            "SKF 6206",
            "SKF 6207",
            "SKF 6208",
            "SKF 6300",
            "SKF bearing deep groove",
        ]
    )

    _split_lists = field_validator("cors_origins", "search_queries", mode="before")(_split_csv)

    @computed_field
    @property
    def proxy_pool(self) -> List[str]:
        return [proxy.strip() for proxy in self.proxy_list.split(",") if proxy.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"production", "prod"}

    @model_validator(mode="after")
    def _reject_insecure_production_key(self) -> Settings:
        if self.is_production and self.api_key in INSECURE_API_KEYS:
            raise ValueError("API_KEY must be set to a strong secret when APP_ENV=production")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.json_log_file.parent.mkdir(parents=True, exist_ok=True)
    return settings
