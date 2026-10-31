from __future__ import annotations

import scrapy


class ASINItem(scrapy.Item):
    asin = scrapy.Field()
    title = scrapy.Field()
    category = scrapy.Field()
    search_query = scrapy.Field()
    price = scrapy.Field()
    seller_hint = scrapy.Field()
    source = scrapy.Field()


class ProductDetailItem(scrapy.Item):
    asin = scrapy.Field()
    title = scrapy.Field()
    mrp = scrapy.Field()
    current_price = scrapy.Field()
    buy_box_seller_name = scrapy.Field()
    stock_status = scrapy.Field()
    simulated_pincode = scrapy.Field()
    source = scrapy.Field()


class SellerOfferItem(scrapy.Item):
    asin = scrapy.Field()
    seller_name = scrapy.Field()
    seller_id_amazon = scrapy.Field()
    price = scrapy.Field()
    shipping_cost = scrapy.Field()
    is_fba = scrapy.Field()
    condition = scrapy.Field()
    is_buy_box_winner = scrapy.Field()
    simulated_pincode = scrapy.Field()
    source = scrapy.Field()

