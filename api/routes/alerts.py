from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.pagination import Page, page_params, set_total
from config.settings import get_settings
from data_pipeline.alert_engine import detect_alerts, render_alert_payload
from data_pipeline.validator import AlertConfig
from db import crud
from db.database import get_db_session


router = APIRouter(tags=["alerts"])
AlertType = Literal["price_drop", "buybox_change", "stock_spike"]
CSV_COLUMNS = [
    "id", "asin", "title", "alert_type", "old_value", "new_value", "triggered_at", "notified", "acknowledged",
]


class AcknowledgePayload(BaseModel):
    acknowledged: bool = True


@router.get("/alerts")
async def list_alerts(
    response: Response,
    type: AlertType | None = Query(default=None),
    acknowledged: bool | None = Query(default=None),
    asin: str | None = Query(default=None, max_length=32),
    page: Page = Depends(page_params),
    session: AsyncSession = Depends(get_db_session),
):
    asin_code = asin.strip().upper() if asin else None
    set_total(response, await crud.count_alerts(session, type, acknowledged, asin_code))
    return await crud.list_alerts(
        session,
        alert_type=type,
        acknowledged=acknowledged,
        asin=asin_code,
        limit=page.limit,
        offset=page.offset,
    )


@router.get("/alerts/export.csv")
async def export_alerts(
    type: AlertType | None = Query(default=None),
    acknowledged: bool | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
):
    rows = await crud.list_alerts(session, alert_type=type, acknowledged=acknowledged)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({**row, "triggered_at": row["triggered_at"].isoformat() if row["triggered_at"] else ""})
    filename = f"bearingpulse-alerts-{datetime.now():%Y%m%d-%H%M}.csv"
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.patch("/alerts/{alert_id}")
async def update_alert(
    alert_id: str,
    payload: AcknowledgePayload = Body(...),
    session: AsyncSession = Depends(get_db_session),
):
    alert = await crud.set_alert_acknowledged(session, alert_id, payload.acknowledged)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    await session.commit()
    return alert


@router.post("/alerts/acknowledge-all")
async def acknowledge_all(
    type: AlertType | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
):
    updated = await crud.acknowledge_all_alerts(session, alert_type=type)
    await session.commit()
    return {"status": "ok", "updated": updated}


@router.post("/alerts/check")
async def run_alert_check(session: AsyncSession = Depends(get_db_session)):
    """Run alert detection against stored snapshots immediately."""
    alerts = await detect_alerts(session)
    return {"status": "ok", "created": len(alerts), "alerts": render_alert_payload(alerts)}


@router.get("/alerts/config")
async def get_alert_config(session: AsyncSession = Depends(get_db_session)):
    configs = await crud.list_alert_configs(session)
    if not any(config["scope"] == crud.DEFAULT_SCOPE for config in configs):
        settings = get_settings()
        configs.insert(
            0,
            {
                "scope": crud.DEFAULT_SCOPE,
                "asin_id": None,
                "threshold_pct": settings.alert_threshold_pct,
                "alert_email": settings.alert_email,
                "updated_at": None,
            },
        )
    return configs


@router.post("/alerts/config")
async def set_alert_config(
    payload: AlertConfig = Body(...),
    session: AsyncSession = Depends(get_db_session),
):
    scope = payload.asin_id or crud.DEFAULT_SCOPE
    if payload.asin_id and await crud.get_asin_by_code(session, payload.asin_id) is None:
        raise HTTPException(status_code=404, detail=f"{payload.asin_id} is not a tracked ASIN")
    config = await crud.upsert_alert_config(session, scope, payload.threshold_pct, payload.alert_email)
    await session.commit()
    return {"status": "ok", "config": config}


@router.delete("/alerts/config/{asin}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert_config(asin: str, session: AsyncSession = Depends(get_db_session)):
    scope = asin.strip().upper()
    if scope.lower() == crud.DEFAULT_SCOPE:
        raise HTTPException(status_code=400, detail="The default threshold cannot be deleted")
    if not await crud.delete_alert_config(session, scope):
        raise HTTPException(status_code=404, detail="No override exists for this ASIN")
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
