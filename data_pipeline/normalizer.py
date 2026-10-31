from __future__ import annotations

import re
from enum import StrEnum


class StockStatus(StrEnum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"


def normalize_price(value: str | float | int | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, (float, int)):
        return float(value)
    cleaned = value.replace("₹", "").replace(",", "").strip()
    if not cleaned:
        return None
    return float(cleaned)


def normalize_seller_name(name: str | None) -> str:
    if not name:
        return ""
    return re.sub(r"\s+", " ", name).strip().lower()


def detect_fba(text: str | None) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return "fulfilled by amazon" in lowered or "amazon fulfilled" in lowered


def map_stock_status(text: str | None) -> StockStatus:
    if not text:
        return StockStatus.OUT_OF_STOCK
    lowered = text.strip().lower()
    if "currently unavailable" in lowered or "out of stock" in lowered:
        return StockStatus.OUT_OF_STOCK
    if "only" in lowered and "left" in lowered:
        return StockStatus.LOW_STOCK
    if "in stock" in lowered or "available" in lowered:
        return StockStatus.IN_STOCK
    return StockStatus.OUT_OF_STOCK

