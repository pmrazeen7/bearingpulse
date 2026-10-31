from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.pagination import Page, page_params, set_total
from db import crud
from db.database import get_db_session


router = APIRouter(tags=["sellers"])


@router.get("/sellers")
async def list_sellers(
    response: Response,
    q: str | None = Query(default=None, max_length=100, description="Search seller name or Amazon ID"),
    page: Page = Depends(page_params),
    session: AsyncSession = Depends(get_db_session),
):
    set_total(response, await crud.count_sellers(session, q))
    return await crud.list_sellers_with_stats(session, q=q, limit=page.limit, offset=page.offset)


@router.get("/sellers/{seller_id}")
async def seller_detail(seller_id: str, session: AsyncSession = Depends(get_db_session)):
    seller = await crud.get_seller(session, seller_id)
    if seller is None:
        raise HTTPException(status_code=404, detail="Seller not found")
    return seller


@router.get("/sellers/{seller_id}/asins")
async def seller_asins(seller_id: str, session: AsyncSession = Depends(get_db_session)):
    if await crud.get_seller(session, seller_id) is None:
        raise HTTPException(status_code=404, detail="Seller not found")
    return await crud.get_seller_asins(session, seller_id)
