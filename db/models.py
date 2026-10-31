from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


def _uuid_column():
    return mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ASIN(Base):
    __tablename__ = "asins"

    id: Mapped[uuid.UUID] = _uuid_column()
    asin: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(255))
    search_query: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=_utcnow
    )

    price_snapshots: Mapped[list[PriceSnapshot]] = relationship(back_populates="asin")
    alerts: Mapped[list[Alert]] = relationship(back_populates="asin")


class Seller(Base):
    __tablename__ = "sellers"

    id: Mapped[uuid.UUID] = _uuid_column()
    seller_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    seller_id_amazon: Mapped[str | None] = mapped_column(String(255))
    is_fba: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    location_state: Mapped[str | None] = mapped_column(String(255))

    price_snapshots: Mapped[list[PriceSnapshot]] = relationship(back_populates="seller")


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"
    __table_args__ = (
        Index("ix_price_snapshots_asin_scraped", "asin_id", "scraped_at"),
        Index("ix_price_snapshots_seller_id", "seller_id"),
    )

    id: Mapped[uuid.UUID] = _uuid_column()
    asin_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("asins.id"), nullable=False)
    seller_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sellers.id"), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    mrp: Mapped[float | None] = mapped_column(Numeric(10, 2))
    discount_pct: Mapped[float | None] = mapped_column(Numeric(5, 2))
    is_buy_box_winner: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    stock_status: Mapped[str | None] = mapped_column(String(64))
    simulated_pincode: Mapped[str | None] = mapped_column(String(16))
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, default=_utcnow)

    asin: Mapped[ASIN] = relationship(back_populates="price_snapshots")
    seller: Mapped[Seller] = relationship(back_populates="price_snapshots")


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (Index("ix_alerts_triggered_at", "triggered_at"),)

    id: Mapped[uuid.UUID] = _uuid_column()
    asin_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("asins.id"), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(64), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    notified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    asin: Mapped[ASIN] = relationship(back_populates="alerts")


class AlertConfig(Base):
    """Price-drop threshold; scope is ``default`` or an ASIN code for an override."""

    __tablename__ = "alert_configs"

    id: Mapped[uuid.UUID] = _uuid_column()
    scope: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    threshold_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    alert_email: Mapped[str | None] = mapped_column(String(255))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )
