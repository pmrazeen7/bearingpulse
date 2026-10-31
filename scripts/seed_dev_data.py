"""Populate a *development* database with synthetic price history.

This exists only so the dashboard can be explored without running the crawler.
It refuses to run when APP_ENV=production. Usage:

    python -m scripts.seed_dev_data [--days 30]
"""

from __future__ import annotations

import argparse
import asyncio
import random
from datetime import UTC, datetime, timedelta

from config.settings import get_settings
from db import crud
from db.database import AsyncSessionLocal


PRODUCTS = [
    ("B08DEMO001", "SKF 6205-2RS1 Deep Groove Ball Bearing 25x52x15mm", "SKF 6205", 640),
    ("B08DEMO002", "SKF 6206-2Z Deep Groove Ball Bearing 30x62x16mm", "SKF 6206", 820),
    ("B08DEMO003", "SKF 6207 Deep Groove Ball Bearing 35x72x17mm", "SKF 6207", 1090),
    ("B08DEMO004", "SKF 6300-2RS Deep Groove Ball Bearing 10x35x11mm", "SKF 6300", 410),
]
SELLERS = [("Chennai Bearings Co", True), ("Precision Hub India", False), ("Southern Industrial Supply", False), ("Appario Retail", True)]
PINS = ["600001", "600017", "641001", "560001"]


async def main(days: int) -> None:
    if get_settings().is_production:
        raise SystemExit("Refusing to seed demo data when APP_ENV=production")
    rng = random.Random(7)
    now = datetime.now(UTC)
    async with AsyncSessionLocal() as session:
        for asin, title, query, base in PRODUCTS:
            await crud.upsert_asin(session, asin=asin, title=title, search_query=query)
            offsets = {name: rng.uniform(-0.06, 0.08) for name, _ in SELLERS}
            for step in range(days * 4):
                when = now - timedelta(hours=(days * 24) - step * 6)
                drift = 1 + 0.06 * rng.uniform(-1, 1) + (0.04 if step % 40 < 8 else 0)
                offers = []
                for name, fba in SELLERS:
                    if rng.random() < 0.15:
                        continue
                    offers.append((name, fba, round(base * drift * (1 + offsets[name] + rng.uniform(-0.02, 0.02)), 2)))
                if not offers:
                    continue
                winner = min(offers, key=lambda o: o[2])[0]
                stock = "out_of_stock" if rng.random() < 0.04 else ("low_stock" if rng.random() < 0.1 else "in_stock")
                for name, fba, price in offers:
                    await crud.create_price_snapshot(
                        session, asin=asin, seller_name=name, price=price, mrp=round(base * 1.35, 2),
                        is_buy_box_winner=name == winner, stock_status=stock, is_fba=fba,
                        location_state="Tamil Nadu", simulated_pincode=rng.choice(PINS), scraped_at=when,
                    )
        await session.commit()
    print(f"Seeded {len(PRODUCTS)} products over {days} days.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30)
    asyncio.run(main(parser.parse_args().days))
