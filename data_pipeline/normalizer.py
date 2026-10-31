from __future__ import annotations

import re
from enum import StrEnum


class StockStatus(StrEnum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"


_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def normalize_price(value: str | float | int | None) -> float | None:
    """Return the first number in ``value``, or None when there is none.

    Amazon renders prices as text like ``₹1,999.00``, ``₹ 839`` or, for a struck-through
    MRP, the same figure twice (``₹1,999 ₹1,999``), so a plain ``float(...)`` is not safe.
    """
    if value is None:
        return None
    if isinstance(value, (float, int)):
        return float(value)
    match = _NUMBER.search(value)
    return float(match.group().replace(",", "")) if match else None


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

