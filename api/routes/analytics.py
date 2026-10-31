from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db import crud
from db.database import get_db_session


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
async def overview(
    days: int = Query(default=14, ge=7, le=90, description="Length of the activity series"),
    session: AsyncSession = Depends(get_db_session),
):
    return await crud.get_overview(session, activity_days=days)


@router.get("/price-leaders")
async def price_leaders(
    days: int | None = Query(default=None, ge=1, le=365),
    session: AsyncSession = Depends(get_db_session),
):
    return await crud.get_price_leaders(session, days=days)


@router.get("/undercut-events")
async def undercut_events(
    days: int | None = Query(default=None, ge=1, le=365),
    limit: int = Query(default=200, ge=1, le=1000),
    session: AsyncSession = Depends(get_db_session),
):
    return (await crud.get_undercut_events(session, days=days))[:limit]
