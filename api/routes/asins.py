from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.pagination import Page, page_params, set_total
from data_pipeline.validator import ASINRecord
from db import crud
from db.database import get_db_session


router = APIRouter(tags=["asins"])


async def _require_asin(session: AsyncSession, asin: str) -> str:
    code = asin.strip().upper()
    if await crud.get_asin_by_code(session, code) is None:
        raise HTTPException(status_code=404, detail="ASIN not found")
    return code


@router.get("/asins")
async def list_asins(
    response: Response,
    q: str | None = Query(default=None, max_length=100, description="Search ASIN, title or query"),
    page: Page = Depends(page_params),
    session: AsyncSession = Depends(get_db_session),
):
    set_total(response, await crud.count_asins(session, q))
    return await crud.list_asins_with_latest_prices(session, q=q, limit=page.limit, offset=page.offset)


@router.post("/asins", status_code=status.HTTP_201_CREATED)
async def track_asin(
    record: ASINRecord = Body(..., examples=[{"asin": "B07XYZ1234", "title": "SKF 6205-2Z"}]),
    session: AsyncSession = Depends(get_db_session),
):
    if await crud.get_asin_by_code(session, record.asin) is not None:
        raise HTTPException(status_code=409, detail=f"{record.asin} is already tracked")
    await crud.upsert_asin(
        session,
        asin=record.asin,
        title=record.title,
        category=record.category,
        search_query=record.search_query,
    )
    await session.commit()
    return await crud.get_asin_detail(session, record.asin)


@router.get("/asins/{asin}")
async def asin_detail(asin: str, session: AsyncSession = Depends(get_db_session)):
    detail = await crud.get_asin_detail(session, asin.strip().upper())
    if detail is None:
        raise HTTPException(status_code=404, detail="ASIN not found")
    return detail


@router.delete("/asins/{asin}", status_code=status.HTTP_204_NO_CONTENT)
async def untrack_asin(asin: str, session: AsyncSession = Depends(get_db_session)):
    if not await crud.delete_asin(session, asin.strip().upper()):
        raise HTTPException(status_code=404, detail="ASIN not found")
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/asins/{asin}/prices")
async def asin_prices(
    asin: str,
    days: int = Query(default=7, ge=1, le=90),
    session: AsyncSession = Depends(get_db_session),
):
    if days not in {7, 30, 90}:
        raise HTTPException(status_code=422, detail="days must be one of 7, 30, 90")
    code = await _require_asin(session, asin)
    return await crud.get_asin_price_history(session, code, days=int(days))


@router.get("/asins/{asin}/sellers")
async def asin_sellers(asin: str, session: AsyncSession = Depends(get_db_session)):
    code = await _require_asin(session, asin)
    return await crud.get_asin_sellers(session, code)


@router.get("/asins/{asin}/buybox-history")
async def buybox_history(asin: str, session: AsyncSession = Depends(get_db_session)):
    code = await _require_asin(session, asin)
    return await crud.get_buybox_history(session, code)
