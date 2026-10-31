
import pytest

from db import crud


@pytest.mark.asyncio
async def test_upsert_and_price_history(db_session):
    await crud.upsert_asin(db_session, asin="B012345678", title="SKF 6205")
    await crud.create_price_snapshot(
        db_session,
        asin="B012345678",
        seller_name="Seller One",
        price=1000.0,
        is_buy_box_winner=True,
        stock_status="in_stock",
    )
    await db_session.commit()

    history = await crud.get_asin_price_history(db_session, "B012345678", days=7)
    assert len(history) == 1
    assert history[0]["price"] == 1000.0


@pytest.mark.asyncio
async def test_list_asins_with_latest_prices(db_session):
    await crud.create_price_snapshot(
        db_session,
        asin="B112345678",
        seller_name="Seller Two",
        price=950.0,
        is_buy_box_winner=True,
        stock_status="in_stock",
    )
    await db_session.commit()

    rows = await crud.list_asins_with_latest_prices(db_session)
    assert any(row["asin"] == "B112345678" for row in rows)
