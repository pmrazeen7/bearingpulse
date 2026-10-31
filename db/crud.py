from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, and_, case, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import ASIN, Alert, AlertConfig, PriceSnapshot, Seller


DEFAULT_SCOPE = "default"


def _as_float(value: Decimal | float | None) -> float | None:
    return float(value) if value is not None else None


def _like(term: str) -> str:
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped.lower()}%"


def _parse_uuid(value: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------- writes


async def upsert_asin(
    session: AsyncSession,
    asin: str,
    title: str | None = None,
    category: str | None = None,
    search_query: str | None = None,
) -> ASIN:
    record = await session.scalar(select(ASIN).where(ASIN.asin == asin))
    if record is None:
        record = ASIN(asin=asin, title=title, category=category, search_query=search_query)
        session.add(record)
        await session.flush()
    else:
        if title:
            record.title = title
        if category:
            record.category = category
        if search_query:
            record.search_query = search_query
    return record


async def upsert_seller(
    session: AsyncSession,
    seller_name: str,
    seller_id_amazon: str | None = None,
    is_fba: bool = False,
    location_state: str | None = None,
) -> Seller:
    stmt = select(Seller).where(func.lower(Seller.seller_name) == seller_name.lower())
    record = await session.scalar(stmt)
    if record is None:
        record = Seller(
            seller_name=seller_name,
            seller_id_amazon=seller_id_amazon,
            is_fba=is_fba,
            location_state=location_state,
        )
        session.add(record)
        await session.flush()
    else:
        record.seller_id_amazon = seller_id_amazon or record.seller_id_amazon
        record.is_fba = is_fba or record.is_fba
        record.location_state = location_state or record.location_state
    return record


async def create_price_snapshot(
    session: AsyncSession,
    asin: str,
    seller_name: str,
    price: float,
    mrp: float | None = None,
    discount_pct: float | None = None,
    is_buy_box_winner: bool = False,
    stock_status: str | None = None,
    simulated_pincode: str | None = None,
    seller_id_amazon: str | None = None,
    is_fba: bool = False,
    location_state: str | None = None,
    scraped_at: datetime | None = None,
) -> PriceSnapshot:
    asin_record = await upsert_asin(session, asin=asin)
    seller_record = await upsert_seller(
        session,
        seller_name=seller_name,
        seller_id_amazon=seller_id_amazon,
        is_fba=is_fba,
        location_state=location_state,
    )
    if discount_pct is None and mrp and mrp > 0 and price < mrp:
        discount_pct = round((mrp - price) / mrp * 100, 2)
    snapshot = PriceSnapshot(
        asin_id=asin_record.id,
        seller_id=seller_record.id,
        price=price,
        mrp=mrp,
        discount_pct=discount_pct,
        is_buy_box_winner=is_buy_box_winner,
        stock_status=stock_status,
        simulated_pincode=simulated_pincode,
    )
    if scraped_at is not None:
        snapshot.scraped_at = scraped_at
    session.add(snapshot)
    await session.flush()
    return snapshot


async def create_alert(
    session: AsyncSession,
    asin_id: uuid.UUID,
    alert_type: str,
    old_value: str | None,
    new_value: str | None,
    notified: bool = False,
) -> Alert:
    alert = Alert(
        asin_id=asin_id,
        alert_type=alert_type,
        old_value=old_value,
        new_value=new_value,
        notified=notified,
    )
    session.add(alert)
    await session.flush()
    return alert


async def delete_asin(session: AsyncSession, asin: str) -> bool:
    """Stop tracking an ASIN, removing its snapshots, alerts and threshold override."""
    record = await get_asin_by_code(session, asin)
    if record is None:
        return False
    await session.execute(delete(PriceSnapshot).where(PriceSnapshot.asin_id == record.id))
    await session.execute(delete(Alert).where(Alert.asin_id == record.id))
    await session.execute(delete(AlertConfig).where(AlertConfig.scope == record.asin))
    await session.delete(record)
    await session.flush()
    return True


# --------------------------------------------------------------------------- ASINs


def _asin_filter(q: str | None):
    if not q:
        return None
    pattern = _like(q.strip())
    return or_(
        func.lower(ASIN.asin).like(pattern, escape="\\"),
        func.lower(func.coalesce(ASIN.title, "")).like(pattern, escape="\\"),
        func.lower(func.coalesce(ASIN.search_query, "")).like(pattern, escape="\\"),
    )


async def count_asins(session: AsyncSession, q: str | None = None) -> int:
    stmt = select(func.count(ASIN.id))
    condition = _asin_filter(q)
    if condition is not None:
        stmt = stmt.where(condition)
    return int(await session.scalar(stmt) or 0)


async def list_asins_with_latest_prices(
    session: AsyncSession,
    q: str | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[dict[str, Any]]:
    ranked = select(
        PriceSnapshot.id.label("snapshot_id"),
        PriceSnapshot.asin_id.label("asin_id"),
        func.row_number()
        .over(
            partition_by=PriceSnapshot.asin_id,
            order_by=(PriceSnapshot.scraped_at.desc(), PriceSnapshot.id.desc()),
        )
        .label("rn"),
    ).subquery()
    latest = select(ranked.c.asin_id, ranked.c.snapshot_id).where(ranked.c.rn == 1).subquery()
    stats = (
        select(
            PriceSnapshot.asin_id.label("asin_id"),
            func.count(PriceSnapshot.id).label("snapshot_count"),
            func.count(func.distinct(PriceSnapshot.seller_id)).label("seller_count"),
            func.min(PriceSnapshot.price).label("min_price"),
            func.max(PriceSnapshot.price).label("max_price"),
        )
        .group_by(PriceSnapshot.asin_id)
        .subquery()
    )
    stmt = (
        select(
            ASIN,
            PriceSnapshot,
            Seller,
            stats.c.snapshot_count,
            stats.c.seller_count,
            stats.c.min_price,
            stats.c.max_price,
        )
        .join(latest, latest.c.asin_id == ASIN.id, isouter=True)
        .join(PriceSnapshot, PriceSnapshot.id == latest.c.snapshot_id, isouter=True)
        .join(Seller, Seller.id == PriceSnapshot.seller_id, isouter=True)
        .join(stats, stats.c.asin_id == ASIN.id, isouter=True)
        .order_by(ASIN.created_at.desc(), ASIN.asin.asc())
    )
    condition = _asin_filter(q)
    if condition is not None:
        stmt = stmt.where(condition)
    if limit is not None:
        stmt = stmt.limit(limit).offset(offset)
    rows = (await session.execute(stmt)).all()
    return [
        {
            "asin": asin.asin,
            "title": asin.title,
            "category": asin.category,
            "search_query": asin.search_query,
            "created_at": asin.created_at,
            "latest_price": _as_float(snapshot.price) if snapshot else None,
            "latest_mrp": _as_float(snapshot.mrp) if snapshot else None,
            "latest_seller": seller.seller_name if seller else None,
            "latest_stock_status": snapshot.stock_status if snapshot else None,
            "latest_scraped_at": snapshot.scraped_at if snapshot else None,
            "snapshot_count": int(snapshot_count or 0),
            "seller_count": int(seller_count or 0),
            "min_price": _as_float(min_price),
            "max_price": _as_float(max_price),
        }
        for asin, snapshot, seller, snapshot_count, seller_count, min_price, max_price in rows
    ]


async def get_asin_detail(session: AsyncSession, asin: str) -> dict[str, Any] | None:
    record = await get_asin_by_code(session, asin)
    if record is None:
        return None
    stats = (
        await session.execute(
            select(
                func.count(PriceSnapshot.id),
                func.count(func.distinct(PriceSnapshot.seller_id)),
                func.min(PriceSnapshot.price),
                func.max(PriceSnapshot.price),
                func.avg(PriceSnapshot.price),
                func.min(PriceSnapshot.scraped_at),
                func.max(PriceSnapshot.scraped_at),
            ).where(PriceSnapshot.asin_id == record.id)
        )
    ).one()
    latest_rows = (
        await session.execute(
            select(PriceSnapshot, Seller)
            .join(Seller, Seller.id == PriceSnapshot.seller_id)
            .where(PriceSnapshot.asin_id == record.id)
            .order_by(PriceSnapshot.scraped_at.desc(), PriceSnapshot.id.desc())
            .limit(1)
        )
    ).first()
    buy_box = (
        await session.execute(
            select(PriceSnapshot, Seller)
            .join(Seller, Seller.id == PriceSnapshot.seller_id)
            .where(PriceSnapshot.asin_id == record.id, PriceSnapshot.is_buy_box_winner.is_(True))
            .order_by(PriceSnapshot.scraped_at.desc(), PriceSnapshot.id.desc())
            .limit(2)
        )
    ).all()
    alert_count = await session.scalar(select(func.count(Alert.id)).where(Alert.asin_id == record.id))
    latest_snapshot, latest_seller = latest_rows if latest_rows else (None, None)
    current_bb = buy_box[0] if buy_box else None
    previous_bb = buy_box[1] if len(buy_box) > 1 else None
    price_change_pct = None
    if current_bb and previous_bb and float(previous_bb[0].price) > 0:
        previous_price = float(previous_bb[0].price)
        price_change_pct = round((float(current_bb[0].price) - previous_price) / previous_price * 100, 2)
    snapshot_count, seller_count, min_price, max_price, avg_price, first_seen, last_seen = stats
    return {
        "asin": record.asin,
        "title": record.title,
        "category": record.category,
        "search_query": record.search_query,
        "created_at": record.created_at,
        "snapshot_count": int(snapshot_count or 0),
        "seller_count": int(seller_count or 0),
        "alert_count": int(alert_count or 0),
        "min_price": _as_float(min_price),
        "max_price": _as_float(max_price),
        "avg_price": round(float(avg_price), 2) if avg_price is not None else None,
        "first_seen": first_seen,
        "last_seen": last_seen,
        "latest_price": _as_float(latest_snapshot.price) if latest_snapshot else None,
        "latest_mrp": _as_float(latest_snapshot.mrp) if latest_snapshot else None,
        "latest_seller": latest_seller.seller_name if latest_seller else None,
        "latest_stock_status": latest_snapshot.stock_status if latest_snapshot else None,
        "buy_box_seller": current_bb[1].seller_name if current_bb else None,
        "buy_box_price": _as_float(current_bb[0].price) if current_bb else None,
        "buy_box_change_pct": price_change_pct,
    }


async def get_asin_price_history(session: AsyncSession, asin: str, days: int = 7) -> list[dict[str, Any]]:
    cutoff = datetime.now(UTC) - timedelta(days=days)
    stmt = (
        select(PriceSnapshot, Seller)
        .join(ASIN, ASIN.id == PriceSnapshot.asin_id)
        .join(Seller, Seller.id == PriceSnapshot.seller_id)
        .where(and_(ASIN.asin == asin, PriceSnapshot.scraped_at >= cutoff))
        .order_by(PriceSnapshot.scraped_at.asc())
    )
    rows = (await session.execute(stmt)).all()
    return [
        {
            "seller_id": str(seller.id),
            "seller_name": seller.seller_name,
            "price": _as_float(snapshot.price),
            "mrp": _as_float(snapshot.mrp),
            "discount_pct": _as_float(snapshot.discount_pct),
            "is_buy_box_winner": snapshot.is_buy_box_winner,
            "stock_status": snapshot.stock_status,
            "simulated_pincode": snapshot.simulated_pincode,
            "scraped_at": snapshot.scraped_at,
        }
        for snapshot, seller in rows
    ]


async def get_asin_sellers(session: AsyncSession, asin: str) -> list[dict[str, Any]]:
    """Latest offer from each seller for one ASIN, cheapest first."""
    record = await get_asin_by_code(session, asin)
    if record is None:
        return []
    ranked = (
        select(
            PriceSnapshot.id.label("snapshot_id"),
            func.row_number()
            .over(
                partition_by=PriceSnapshot.seller_id,
                order_by=(PriceSnapshot.scraped_at.desc(), PriceSnapshot.id.desc()),
            )
            .label("rn"),
        )
        .where(PriceSnapshot.asin_id == record.id)
        .subquery()
    )
    stmt = (
        select(Seller, PriceSnapshot)
        .join(PriceSnapshot, PriceSnapshot.seller_id == Seller.id)
        .join(ranked, and_(ranked.c.snapshot_id == PriceSnapshot.id, ranked.c.rn == 1))
        .order_by(PriceSnapshot.price.asc())
    )
    rows = (await session.execute(stmt)).all()
    return [
        {
            "seller_id": str(seller.id),
            "seller_name": seller.seller_name,
            "is_fba": seller.is_fba,
            "location_state": seller.location_state,
            "current_price": _as_float(snapshot.price),
            "mrp": _as_float(snapshot.mrp),
            "stock_status": snapshot.stock_status,
            "is_buy_box_winner": snapshot.is_buy_box_winner,
            "simulated_pincode": snapshot.simulated_pincode,
            "scraped_at": snapshot.scraped_at,
        }
        for seller, snapshot in rows
    ]


async def get_buybox_history(session: AsyncSession, asin: str) -> list[dict[str, Any]]:
    stmt = (
        select(PriceSnapshot, Seller)
        .join(ASIN, ASIN.id == PriceSnapshot.asin_id)
        .join(Seller, Seller.id == PriceSnapshot.seller_id)
        .where(and_(ASIN.asin == asin, PriceSnapshot.is_buy_box_winner.is_(True)))
        .order_by(PriceSnapshot.scraped_at.asc())
    )
    rows = (await session.execute(stmt)).all()
    return [
        {
            "seller_id": str(seller.id),
            "seller_name": seller.seller_name,
            "price": _as_float(snapshot.price),
            "simulated_pincode": snapshot.simulated_pincode,
            "scraped_at": snapshot.scraped_at,
        }
        for snapshot, seller in rows
    ]


# --------------------------------------------------------------------------- sellers


def _seller_filter(q: str | None):
    if not q:
        return None
    pattern = _like(q.strip())
    return or_(
        func.lower(Seller.seller_name).like(pattern, escape="\\"),
        func.lower(func.coalesce(Seller.seller_id_amazon, "")).like(pattern, escape="\\"),
    )


async def count_sellers(session: AsyncSession, q: str | None = None) -> int:
    stmt = select(func.count(Seller.id))
    condition = _seller_filter(q)
    if condition is not None:
        stmt = stmt.where(condition)
    return int(await session.scalar(stmt) or 0)


def _seller_stats_stmt() -> Select[Any]:
    return (
        select(
            Seller,
            func.count(func.distinct(PriceSnapshot.asin_id)).label("asin_count"),
            func.min(PriceSnapshot.price).label("best_price"),
            func.count(PriceSnapshot.id).label("snapshot_count"),
            func.sum(case((PriceSnapshot.is_buy_box_winner.is_(True), 1), else_=0)).label("buy_box_wins"),
            func.max(PriceSnapshot.scraped_at).label("last_seen"),
        )
        .join(PriceSnapshot, PriceSnapshot.seller_id == Seller.id, isouter=True)
        .group_by(Seller.id)
    )


def _seller_row(seller: Seller, asin_count, best_price, snapshot_count, buy_box_wins, last_seen) -> dict[str, Any]:
    return {
        "seller_id": str(seller.id),
        "seller_name": seller.seller_name,
        "seller_id_amazon": seller.seller_id_amazon,
        "is_fba": seller.is_fba,
        "location_state": seller.location_state,
        "asin_count": int(asin_count or 0),
        "best_price": _as_float(best_price),
        "snapshot_count": int(snapshot_count or 0),
        "buy_box_wins": int(buy_box_wins or 0),
        "last_seen": last_seen,
    }


async def list_sellers_with_stats(
    session: AsyncSession,
    q: str | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[dict[str, Any]]:
    stmt = _seller_stats_stmt().order_by(Seller.seller_name.asc())
    condition = _seller_filter(q)
    if condition is not None:
        stmt = stmt.where(condition)
    if limit is not None:
        stmt = stmt.limit(limit).offset(offset)
    rows = (await session.execute(stmt)).all()
    return [_seller_row(*row) for row in rows]


async def get_seller(session: AsyncSession, seller_id: str) -> dict[str, Any] | None:
    parsed = _parse_uuid(seller_id)
    if parsed is None:
        return None
    row = (await session.execute(_seller_stats_stmt().where(Seller.id == parsed))).first()
    return _seller_row(*row) if row else None


async def get_seller_asins(session: AsyncSession, seller_id: str) -> list[dict[str, Any]]:
    parsed = _parse_uuid(seller_id)
    if parsed is None:
        return []
    stmt = (
        select(
            ASIN,
            func.min(PriceSnapshot.price).label("best_price"),
            func.count(PriceSnapshot.id).label("snapshot_count"),
            func.max(PriceSnapshot.scraped_at).label("last_seen"),
        )
        .join(PriceSnapshot, PriceSnapshot.asin_id == ASIN.id)
        .where(PriceSnapshot.seller_id == parsed)
        .group_by(ASIN.id)
        .order_by(ASIN.asin.asc())
    )
    rows = (await session.execute(stmt)).all()
    return [
        {
            "asin": asin.asin,
            "title": asin.title,
            "best_price": _as_float(best_price),
            "snapshot_count": int(snapshot_count or 0),
            "last_seen": last_seen,
        }
        for asin, best_price, snapshot_count, last_seen in rows
    ]


# --------------------------------------------------------------------------- analytics


async def _snapshot_groups(
    session: AsyncSession, days: int | None
) -> dict[str, dict[datetime, list[tuple[str, float]]]]:
    stmt = (
        select(ASIN.asin, Seller.seller_name, PriceSnapshot.price, PriceSnapshot.scraped_at)
        .join(ASIN, ASIN.id == PriceSnapshot.asin_id)
        .join(Seller, Seller.id == PriceSnapshot.seller_id)
        .order_by(ASIN.asin.asc(), PriceSnapshot.scraped_at.asc())
    )
    if days:
        stmt = stmt.where(PriceSnapshot.scraped_at >= datetime.now(UTC) - timedelta(days=days))
    grouped: dict[str, dict[datetime, list[tuple[str, float]]]] = defaultdict(lambda: defaultdict(list))
    for asin, seller_name, price, scraped_at in (await session.execute(stmt)).all():
        grouped[asin][scraped_at].append((seller_name, float(price)))
    return grouped


async def get_price_leaders(session: AsyncSession, days: int | None = None) -> list[dict[str, Any]]:
    grouped = await _snapshot_groups(session, days)
    results = []
    for asin, timestamps in grouped.items():
        counts: dict[str, int] = defaultdict(int)
        for samples in timestamps.values():
            min_price = min(price for _, price in samples)
            for seller_name, price in samples:
                if price == min_price:
                    counts[seller_name] += 1
        if counts:
            leader = max(counts.items(), key=lambda item: item[1])
            results.append({"asin": asin, "seller_name": leader[0], "lead_count": leader[1]})
    return results


async def get_undercut_events(session: AsyncSession, days: int | None = None) -> list[dict[str, Any]]:
    grouped = await _snapshot_groups(session, days)
    events: list[dict[str, Any]] = []
    for asin, timestamps in grouped.items():
        previous_best = None
        for scraped_at in sorted(timestamps.keys()):
            samples = timestamps[scraped_at]
            current_best = min(samples, key=lambda item: item[1])
            if previous_best and current_best[1] < previous_best[1]:
                events.append(
                    {
                        "asin": asin,
                        "seller_name": current_best[0],
                        "price": current_best[1],
                        "buy_box_price": previous_best[1],
                        "scraped_at": scraped_at,
                    }
                )
            previous_best = current_best
    events.sort(key=lambda event: event["scraped_at"], reverse=True)
    return events


def _to_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


async def get_overview(session: AsyncSession, activity_days: int = 14) -> dict[str, Any]:
    now = datetime.now(UTC)
    day_ago = now - timedelta(days=1)
    asin_count = await session.scalar(select(func.count(ASIN.id)))
    seller_count = await session.scalar(select(func.count(Seller.id)))
    fba_count = await session.scalar(select(func.count(Seller.id)).where(Seller.is_fba.is_(True)))
    snapshot_count = await session.scalar(select(func.count(PriceSnapshot.id)))
    snapshots_24h = await session.scalar(
        select(func.count(PriceSnapshot.id)).where(PriceSnapshot.scraped_at >= day_ago)
    )
    last_scraped_at = await session.scalar(select(func.max(PriceSnapshot.scraped_at)))
    alert_count = await session.scalar(select(func.count(Alert.id)))
    open_alerts = await session.scalar(select(func.count(Alert.id)).where(Alert.acknowledged.is_(False)))
    alerts_24h = await session.scalar(select(func.count(Alert.id)).where(Alert.triggered_at >= day_ago))
    alert_breakdown = {
        alert_type: int(count)
        for alert_type, count in (
            await session.execute(select(Alert.alert_type, func.count(Alert.id)).group_by(Alert.alert_type))
        ).all()
    }
    stock_breakdown = {
        (status or "unknown"): int(count)
        for status, count in (
            await session.execute(
                select(PriceSnapshot.stock_status, func.count(PriceSnapshot.id))
                .where(PriceSnapshot.scraped_at >= now - timedelta(days=activity_days))
                .group_by(PriceSnapshot.stock_status)
            )
        ).all()
    }

    start = (now - timedelta(days=activity_days - 1)).date()
    day_bucket = func.date(PriceSnapshot.scraped_at)
    activity_rows = (
        await session.execute(
            select(day_bucket, func.count(PriceSnapshot.id))
            .where(PriceSnapshot.scraped_at >= datetime.combine(start, datetime.min.time(), tzinfo=UTC))
            .group_by(day_bucket)
        )
    ).all()
    counts_by_day = {_to_date(day): int(count) for day, count in activity_rows}
    days = [start + timedelta(days=offset) for offset in range(activity_days)]
    activity = [{"date": day.isoformat(), "snapshots": counts_by_day.get(day, 0)} for day in days]
    return {
        "asin_count": int(asin_count or 0),
        "seller_count": int(seller_count or 0),
        "fba_seller_count": int(fba_count or 0),
        "snapshot_count": int(snapshot_count or 0),
        "snapshots_24h": int(snapshots_24h or 0),
        "last_scraped_at": last_scraped_at,
        "alert_count": int(alert_count or 0),
        "open_alert_count": int(open_alerts or 0),
        "alerts_24h": int(alerts_24h or 0),
        "alert_breakdown": alert_breakdown,
        "stock_breakdown": stock_breakdown,
        "activity": activity,
    }


# --------------------------------------------------------------------------- alerts


def _alert_filters(stmt, alert_type: str | None, acknowledged: bool | None, asin: str | None):
    if alert_type:
        stmt = stmt.where(Alert.alert_type == alert_type)
    if acknowledged is not None:
        stmt = stmt.where(Alert.acknowledged.is_(acknowledged))
    if asin:
        stmt = stmt.where(ASIN.asin == asin)
    return stmt


async def count_alerts(
    session: AsyncSession,
    alert_type: str | None = None,
    acknowledged: bool | None = None,
    asin: str | None = None,
) -> int:
    stmt = select(func.count(Alert.id)).join(ASIN, ASIN.id == Alert.asin_id)
    return int(await session.scalar(_alert_filters(stmt, alert_type, acknowledged, asin)) or 0)


def _alert_row(alert: Alert, asin: ASIN) -> dict[str, Any]:
    return {
        "id": str(alert.id),
        "asin": asin.asin,
        "title": asin.title,
        "alert_type": alert.alert_type,
        "old_value": alert.old_value,
        "new_value": alert.new_value,
        "triggered_at": alert.triggered_at,
        "notified": alert.notified,
        "acknowledged": alert.acknowledged,
    }


async def list_alerts(
    session: AsyncSession,
    alert_type: str | None = None,
    acknowledged: bool | None = None,
    asin: str | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[dict[str, Any]]:
    stmt: Select[Any] = (
        select(Alert, ASIN)
        .join(ASIN, ASIN.id == Alert.asin_id)
        .order_by(Alert.triggered_at.desc(), Alert.id.desc())
    )
    stmt = _alert_filters(stmt, alert_type, acknowledged, asin)
    if limit is not None:
        stmt = stmt.limit(limit).offset(offset)
    rows = (await session.execute(stmt)).all()
    return [_alert_row(alert, asin_record) for alert, asin_record in rows]


async def set_alert_acknowledged(session: AsyncSession, alert_id: str, acknowledged: bool) -> dict[str, Any] | None:
    parsed = _parse_uuid(alert_id)
    if parsed is None:
        return None
    row = (
        await session.execute(select(Alert, ASIN).join(ASIN, ASIN.id == Alert.asin_id).where(Alert.id == parsed))
    ).first()
    if row is None:
        return None
    alert, asin = row
    alert.acknowledged = acknowledged
    await session.flush()
    return _alert_row(alert, asin)


async def acknowledge_all_alerts(session: AsyncSession, alert_type: str | None = None) -> int:
    stmt = update(Alert).where(Alert.acknowledged.is_(False)).values(acknowledged=True)
    if alert_type:
        stmt = stmt.where(Alert.alert_type == alert_type)
    result = await session.execute(stmt)
    return int(result.rowcount or 0)


async def get_recent_snapshots(session: AsyncSession, asin_id: uuid.UUID) -> list[PriceSnapshot]:
    stmt = (
        select(PriceSnapshot)
        .where(PriceSnapshot.asin_id == asin_id)
        .order_by(PriceSnapshot.scraped_at.desc(), PriceSnapshot.id.desc())
        .limit(2)
    )
    return list((await session.execute(stmt)).scalars().all())


async def get_recent_buybox_snapshots(session: AsyncSession, asin_id: uuid.UUID, limit: int = 2) -> list[PriceSnapshot]:
    stmt = (
        select(PriceSnapshot)
        .where(PriceSnapshot.asin_id == asin_id, PriceSnapshot.is_buy_box_winner.is_(True))
        .order_by(PriceSnapshot.scraped_at.desc(), PriceSnapshot.id.desc())
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars().all())


# --------------------------------------------------------------------------- alert configs


def _config_row(config: AlertConfig) -> dict[str, Any]:
    return {
        "scope": config.scope,
        "asin_id": None if config.scope == DEFAULT_SCOPE else config.scope,
        "threshold_pct": float(config.threshold_pct),
        "alert_email": config.alert_email,
        "updated_at": config.updated_at,
    }


async def list_alert_configs(session: AsyncSession) -> list[dict[str, Any]]:
    rows = (await session.execute(select(AlertConfig).order_by(AlertConfig.scope.asc()))).scalars().all()
    return [_config_row(row) for row in rows]


async def upsert_alert_config(
    session: AsyncSession, scope: str, threshold_pct: float, alert_email: str | None = None
) -> dict[str, Any]:
    record = await session.scalar(select(AlertConfig).where(AlertConfig.scope == scope))
    if record is None:
        record = AlertConfig(scope=scope, threshold_pct=threshold_pct, alert_email=alert_email)
        session.add(record)
    else:
        record.threshold_pct = threshold_pct
        record.alert_email = alert_email
        record.updated_at = datetime.now(UTC)
    await session.flush()
    return _config_row(record)


async def delete_alert_config(session: AsyncSession, scope: str) -> bool:
    result = await session.execute(delete(AlertConfig).where(AlertConfig.scope == scope))
    return bool(result.rowcount)


async def get_threshold_map(session: AsyncSession) -> dict[str, float]:
    rows = (await session.execute(select(AlertConfig.scope, AlertConfig.threshold_pct))).all()
    return {scope: float(threshold) for scope, threshold in rows}


# --------------------------------------------------------------------------- misc


async def get_asin_by_code(session: AsyncSession, asin: str) -> ASIN | None:
    return await session.scalar(select(ASIN).where(ASIN.asin == asin))


async def get_all_asins(session: AsyncSession) -> list[ASIN]:
    return list((await session.execute(select(ASIN).order_by(ASIN.asin.asc()))).scalars().all())


async def healthcheck(session: AsyncSession) -> dict[str, str]:
    await session.execute(select(1))
    return {"db": "ok"}
