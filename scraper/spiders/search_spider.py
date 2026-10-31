from __future__ import annotations

from urllib.parse import quote_plus

import scrapy

from config.settings import get_settings
from data_pipeline.parser import parse_search_results
from scraper.items import ASINItem


class SearchSpider(scrapy.Spider):
    name = "search_spider"
    allowed_domains = ["amazon.in"]

    async def start(self):
        settings = get_settings()
        for query in settings.search_queries:
            for page in range(1, 6):
                url = f"https://www.amazon.in/s?k={quote_plus(query)}&page={page}"
                yield scrapy.Request(url=url, callback=self.parse, meta={"search_query": query, "page": page})

    def parse(self, response):
        for result in parse_search_results(response.text):
            item = ASINItem()
            item["asin"] = result["asin"]
            item["title"] = result["title"]
            item["price"] = result["price"]
            item["seller_hint"] = result["seller_hint"]
            item["search_query"] = response.meta["search_query"]
            item["source"] = "search"
            yield item

