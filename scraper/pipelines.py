from __future__ import annotations

import logging
from typing import Any

from pydantic import ValidationError
from scrapy.exceptions import DropItem

from data_pipeline.validator import ASINRecord, PriceRecord, SellerRecord
from db.crud import create_price_snapshot, upsert_asin, upsert_seller
from db.database import AsyncSessionLocal


logger = logging.getLogger(__name__)


class DatabasePipeline:
    """Validate scraped items and persist them.

    ``process_item`` is a coroutine: Scrapy awaits it on the asyncio reactor
    configured in ``scraper/settings.py``, so database I/O shares the crawler's
    event loop instead of spinning up a second one.
    """

    async def process_item(self, item: Any, spider):
        payload = dict(item)
        source = payload.get("source", "")
        try:
            if source == "search":
                record = ASINRecord(
                    asin=payload["asin"],
                    title=payload.get("title"),
                    search_query=payload.get("search_query"),
                )
                await self._store_asin(record)
            elif source == "product":
                if payload.get("current_price") is None:
                    raise DropItem(f"No price parsed for {payload.get('asin')}")
                record = PriceRecord(
                    asin=payload["asin"],
                    seller_name=payload.get("buy_box_seller_name") or "amazon",
                    price=float(payload["current_price"]),
                    mrp=payload.get("mrp"),
                    is_buy_box_winner=True,
                    stock_status=payload.get("stock_status") or "in_stock",
                    simulated_pincode=payload.get("simulated_pincode"),
                )
                await self._store_product_snapshot(record, payload.get("title"))
            elif source == "offer":
                if payload.get("price") is None:
                    raise DropItem(f"No price parsed for offer on {payload.get('asin')}")
                seller = SellerRecord(
                    seller_name=payload.get("seller_name") or "",
                    seller_id_amazon=payload.get("seller_id_amazon"),
                    is_fba=bool(payload.get("is_fba")),
                )
                record = PriceRecord(
                    asin=payload["asin"],
                    seller_name=seller.seller_name,
                    price=float(payload["price"]),
                    is_buy_box_winner=bool(payload.get("is_buy_box_winner")),
                    stock_status="in_stock",
                    simulated_pincode=payload.get("simulated_pincode"),
                )
                await self._store_offer_snapshot(record, seller)
            else:
                raise DropItem(f"Unknown item source: {source!r}")
        except ValidationError as exc:
            raise DropItem(f"Invalid {source} item: {exc.errors(include_url=False)}") from exc
        return item

    async def _store_asin(self, record: ASINRecord) -> None:
        async with AsyncSessionLocal() as session:
            await upsert_asin(session, asin=record.asin, title=record.title, search_query=record.search_query)
            await session.commit()

    async def _store_product_snapshot(self, record: PriceRecord, title: str | None) -> None:
        async with AsyncSessionLocal() as session:
            await upsert_asin(session, asin=record.asin, title=title)
            await create_price_snapshot(
                session,
                asin=record.asin,
                seller_name=record.seller_name,
                price=record.price,
                mrp=record.mrp,
                is_buy_box_winner=True,
                stock_status=record.stock_status,
                simulated_pincode=record.simulated_pincode,
            )
            await session.commit()

    async def _store_offer_snapshot(self, record: PriceRecord, seller: SellerRecord) -> None:
        async with AsyncSessionLocal() as session:
            await upsert_seller(
                session,
                seller_name=seller.seller_name,
                seller_id_amazon=seller.seller_id_amazon,
                is_fba=seller.is_fba,
                location_state="Tamil Nadu",
            )
            await create_price_snapshot(
                session,
                asin=record.asin,
                seller_name=seller.seller_name,
                price=record.price,
                is_buy_box_winner=record.is_buy_box_winner,
                stock_status=record.stock_status,
                simulated_pincode=record.simulated_pincode,
                seller_id_amazon=seller.seller_id_amazon,
                is_fba=seller.is_fba,
                location_state="Tamil Nadu",
            )
            await session.commit()
