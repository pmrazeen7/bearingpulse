from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import Iterable

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import get_settings
from db import crud
from db.models import Alert


settings = get_settings()
logger = logging.getLogger(__name__)


async def _alert_exists(
    session: AsyncSession,
    asin_id,
    alert_type: str,
    old_value: str | None,
    new_value: str | None,
) -> bool:
    stmt = select(Alert.id).where(
        Alert.asin_id == asin_id,
        Alert.alert_type == alert_type,
        Alert.old_value == old_value,
        Alert.new_value == new_value,
    )
    return await session.scalar(stmt) is not None


async def _create_once(session, alerts: list[Alert], asin_id, alert_type: str, old_value: str, new_value: str) -> None:
    if not await _alert_exists(session, asin_id, alert_type, old_value, new_value):
        alerts.append(
            await crud.create_alert(
                session, asin_id=asin_id, alert_type=alert_type, old_value=old_value, new_value=new_value
            )
        )


async def detect_alerts(session: AsyncSession, threshold_pct: float | None = None) -> list[Alert]:
    """Compare the two most recent Buy Box observations of every ASIN.

    Snapshots from different sellers are not comparable for price movement, so
    price drops and Buy Box changes are measured on the Buy Box winner series.
    Thresholds come from ``alert_configs`` (per-ASIN override, then ``default``),
    then the explicit ``threshold_pct`` argument, then ``ALERT_THRESHOLD_PCT``.
    """
    thresholds = await crud.get_threshold_map(session)
    fallback = thresholds.get(crud.DEFAULT_SCOPE) or threshold_pct or settings.alert_threshold_pct
    alerts: list[Alert] = []
    for asin in await crud.get_all_asins(session):
        threshold = thresholds.get(asin.asin, fallback)
        series = await crud.get_recent_buybox_snapshots(session, asin.id)
        if len(series) < 2:
            series = await crud.get_recent_snapshots(session, asin.id)
        if len(series) < 2:
            continue
        latest, previous = series[0], series[1]
        latest_price = float(latest.price)
        previous_price = float(previous.price)
        if previous_price > 0:
            drop_pct = ((previous_price - latest_price) / previous_price) * 100
            if drop_pct > threshold:
                await _create_once(
                    session, alerts, asin.id, "price_drop", f"{previous_price:.2f}", f"{latest_price:.2f}"
                )
        if latest.is_buy_box_winner and previous.is_buy_box_winner and latest.seller_id != previous.seller_id:
            await _create_once(
                session, alerts, asin.id, "buybox_change", str(previous.seller_id), str(latest.seller_id)
            )
        if previous.stock_status == "in_stock" and latest.stock_status == "out_of_stock":
            await _create_once(session, alerts, asin.id, "stock_spike", previous.stock_status, latest.stock_status)
    await session.commit()
    return alerts


def render_alert_payload(alerts: Iterable[Alert]) -> list[dict]:
    return [
        {
            "alert_id": str(alert.id),
            "asin_id": str(alert.asin_id),
            "alert_type": alert.alert_type,
            "old_value": alert.old_value,
            "new_value": alert.new_value,
            "triggered_at": alert.triggered_at.isoformat() if alert.triggered_at else None,
        }
        for alert in alerts
    ]


async def notify_webhook(webhook_url: str, alerts: Iterable[Alert]) -> None:
    payload = {"alerts": render_alert_payload(alerts)}
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(webhook_url, json=payload)
        response.raise_for_status()


def notify_email(subject: str, body: str) -> bool:
    """Send an alert email. Returns False when SMTP is not configured."""
    if not settings.smtp_user or not settings.smtp_pass:
        logger.info("SMTP credentials not configured; skipping alert email")
        return False
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_user
    message["To"] = settings.alert_email
    message.set_content(body)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_pass)
        server.send_message(message)
    return True


async def mark_alerts_notified(session: AsyncSession, alert_ids: list[str]) -> None:
    if not alert_ids:
        return
    stmt = select(Alert).where(Alert.id.in_(alert_ids))
    for alert in (await session.execute(stmt)).scalars():
        alert.notified = True
    await session.commit()
