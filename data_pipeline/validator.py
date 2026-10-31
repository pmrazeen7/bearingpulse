from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


ASIN_PATTERN = re.compile(r"^[A-Z0-9]{10}$")


class ASINRecord(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    asin: str
    title: Optional[str] = Field(default=None, max_length=500)
    category: Optional[str] = Field(default=None, max_length=255)
    search_query: Optional[str] = Field(default=None, max_length=255)

    @field_validator("asin")
    @classmethod
    def validate_asin(cls, value: str) -> str:
        upper_value = value.upper()
        if not ASIN_PATTERN.fullmatch(upper_value):
            raise ValueError("asin must be 10-char alphanumeric")
        return upper_value


class SellerRecord(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    seller_name: str
    seller_id_amazon: Optional[str] = None
    is_fba: bool = False
    location_state: Optional[str] = None

    @field_validator("seller_name")
    @classmethod
    def validate_seller_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("seller_name must be non-empty")
        return value.strip()


class PriceRecord(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    asin: str
    seller_name: str
    price: float
    mrp: Optional[float] = None
    discount_pct: Optional[float] = None
    is_buy_box_winner: bool = False
    stock_status: str = "in_stock"
    simulated_pincode: Optional[str] = None
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("asin")
    @classmethod
    def validate_asin(cls, value: str) -> str:
        upper_value = value.upper()
        if not ASIN_PATTERN.fullmatch(upper_value):
            raise ValueError("asin must be 10-char alphanumeric")
        return upper_value

    @field_validator("seller_name")
    @classmethod
    def validate_seller_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("seller_name must be non-empty")
        return value.strip()

    @field_validator("price")
    @classmethod
    def validate_price(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("price must be positive")
        return round(float(value), 2)


class AlertConfig(BaseModel):
    """Price-drop threshold; ``asin_id`` is an ASIN code for a per-product override."""

    model_config = ConfigDict(str_strip_whitespace=True)

    threshold_pct: float = Field(gt=0, le=100)
    asin_id: Optional[str] = None
    alert_email: Optional[EmailStr] = None

    @field_validator("asin_id", mode="before")
    @classmethod
    def validate_asin_id(cls, value: Optional[str]) -> Optional[str]:
        if value is None or not str(value).strip():
            return None
        upper_value = str(value).strip().upper()
        if not ASIN_PATTERN.fullmatch(upper_value):
            raise ValueError("asin_id must be a 10-char alphanumeric ASIN")
        return upper_value

    @field_validator("alert_email", mode="before")
    @classmethod
    def blank_email_is_none(cls, value: Optional[str]) -> Optional[str]:
        return value or None
