from __future__ import annotations

import random
import re
from dataclasses import dataclass, field

from config.settings import get_settings


# ScrapeOps Proxy Aggregator "proxy port" mode: the API key is the proxy password,
# so the target URL is fetched unchanged and Scrapy's own proxy handling applies.
SCRAPEOPS_PROXY = "http://scrapeops:{api_key}@proxy.scrapeops.io:5353"
_CREDENTIALS = re.compile(r"(?<=://)[^/@\s]+@")


def redact_proxy(proxy: str | None) -> str | None:
    """Strip ``user:password@`` from a proxy URL so it is safe to log."""
    return _CREDENTIALS.sub("***@", proxy) if proxy else proxy


@dataclass
class ProxyState:
    proxy: str
    attempts: int = 0
    failures: int = 0
    successes: int = 0

    @property
    def health_score(self) -> float:
        total = self.attempts or 1
        return self.successes / total

    @property
    def failure_rate(self) -> float:
        total = self.attempts or 1
        return self.failures / total


@dataclass
class ProxyManager:
    local_proxies: list[str] = field(default_factory=lambda: get_settings().proxy_pool.copy())
    states: dict[str, ProxyState] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.settings = get_settings()
        for proxy in self.local_proxies:
            self.states.setdefault(proxy, ProxyState(proxy=proxy))

    def get_proxy(self, target_url: str | None = None, attempt: int = 0) -> str | None:
        if self.settings.scrapeops_api_key:
            return SCRAPEOPS_PROXY.format(api_key=self.settings.scrapeops_api_key)
        active_local = [
            proxy for proxy, state in self.states.items() if state.failure_rate <= 0.2 or state.attempts < 5
        ]
        return random.choice(active_local) if active_local else None

    def record_success(self, proxy: str | None) -> None:
        if proxy and proxy in self.states:
            state = self.states[proxy]
            state.attempts += 1
            state.successes += 1

    def record_failure(self, proxy: str | None) -> None:
        if proxy and proxy in self.states:
            state = self.states[proxy]
            state.attempts += 1
            state.failures += 1

    def retire_unhealthy(self) -> None:
        for proxy, state in list(self.states.items()):
            if state.failure_rate > 0.2 and state.attempts >= 5:
                self.states.pop(proxy, None)


proxy_manager = ProxyManager()
