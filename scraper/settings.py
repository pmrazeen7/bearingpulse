from __future__ import annotations

from config.settings import get_settings


project_settings = get_settings()

BOT_NAME = "amazon_price_monitor"
SPIDER_MODULES = ["scraper.spiders"]
NEWSPIDER_MODULE = "scraper.spiders"
ROBOTSTXT_OBEY = False
CONCURRENT_REQUESTS = project_settings.max_concurrent_requests
CONCURRENT_REQUESTS_PER_DOMAIN = project_settings.max_concurrent_requests
DOWNLOAD_DELAY = project_settings.download_delay
RANDOMIZE_DOWNLOAD_DELAY = True
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = project_settings.download_delay
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
COOKIES_ENABLED = True
RETRY_ENABLED = False
LOG_LEVEL = "INFO"
ITEM_PIPELINES = {"scraper.pipelines.DatabasePipeline": 300}
DOWNLOADER_MIDDLEWARES = {
    "scraper.middlewares.RandomUserAgentMiddleware": 400,
    "scraper.middlewares.ProxyRotationMiddleware": 410,
    "scraper.middlewares.BlockedResponseRetryMiddleware": 550,
}
HTTPCACHE_ENABLED = False
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
