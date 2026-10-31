from __future__ import annotations

import scrapy

from data_pipeline.parser import parse_product_page
from playwright_scraper.dynamic_scraper import fetch_dynamic_html
from scraper.items import ProductDetailItem


class AsinSpider(scrapy.Spider):
    name = "asin_spider"
    allowed_domains = ["amazon.in"]

    def __init__(self, asins: str = "", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.asins = [asin.strip().upper() for asin in asins.split(",") if asin.strip()]

    async def start(self):
        for asin in self.asins:
            yield scrapy.Request(f"https://www.amazon.in/dp/{asin}", callback=self.parse_detail, meta={"asin": asin})

    async def parse_detail(self, response):
        parsed = parse_product_page(response.text)
        if parsed["is_js_heavy"]:
            # Runs on the crawler's asyncio reactor; no nested event loop.
            try:
                parsed = parse_product_page(await fetch_dynamic_html(response.url))
            except Exception as exc:
                self.logger.warning("Playwright fallback failed for %s: %s", response.url, exc)
        item = ProductDetailItem()
        item["asin"] = response.meta["asin"]
        item["title"] = parsed["title"]
        item["mrp"] = parsed["mrp"]
        item["current_price"] = parsed["current_price"]
        item["buy_box_seller_name"] = parsed["buy_box_seller_name"]
        item["stock_status"] = parsed["stock_status"]
        item["simulated_pincode"] = response.meta.get("simulated_pincode")
        item["source"] = "product"
        yield item
