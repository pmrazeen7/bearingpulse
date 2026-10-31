from __future__ import annotations

import scrapy

from anti_bot.geo_simulator import TAMIL_NADU_PINCODES
from data_pipeline.parser import parse_offer_listing
from scraper.items import SellerOfferItem


class SellerSpider(scrapy.Spider):
    name = "seller_spider"
    allowed_domains = ["amazon.in"]

    def __init__(self, asins: str = "", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.asins = [asin.strip().upper() for asin in asins.split(",") if asin.strip()]
        self.expected_total = len(self.asins) * len(TAMIL_NADU_PINCODES)

    async def start(self):
        for asin in self.asins:
            for pincode in TAMIL_NADU_PINCODES:
                yield scrapy.Request(
                    f"https://www.amazon.in/gp/offer-listing/{asin}",
                    callback=self.parse_offers,
                    meta={"asin": asin, "pincode": pincode},
                )

    def parse_offers(self, response):
        for offer in parse_offer_listing(response.text):
            item = SellerOfferItem()
            item["asin"] = response.meta["asin"]
            item["seller_name"] = offer["seller_name"]
            item["seller_id_amazon"] = offer["seller_id_amazon"]
            item["price"] = offer["price"]
            item["shipping_cost"] = offer["shipping_cost"]
            item["is_fba"] = offer["is_fba"]
            item["condition"] = offer["condition"]
            item["is_buy_box_winner"] = offer["is_buy_box_winner"]
            item["simulated_pincode"] = response.meta["pincode"]
            item["source"] = "offer"
            yield item

