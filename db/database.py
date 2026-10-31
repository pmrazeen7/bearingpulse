from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from config.settings import get_settings


Base = declarative_base()
settings = get_settings()


def normalize_async_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    return url


def normalize_sync_url(url: str) -> str:
    """Return a driver URL usable by synchronous tooling such as Alembic."""
    return url.replace("+asyncpg", "").replace("+aiosqlite", "")


# Kept for backwards compatibility with earlier imports.
_normalize_database_url = normalize_async_url


engine: AsyncEngine = create_async_engine(
    normalize_async_url(settings.database_url),
    pool_pre_ping=True,
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


@asynccontextmanager
async def isolated_session() -> AsyncIterator[AsyncSession]:
    """Session on a throwaway engine.

    Celery tasks call ``asyncio.run`` once per task, so each run has a new event
    loop. Pooled asyncpg connections are bound to the loop that created them, so
    reusing the module-level engine across runs fails. A NullPool engine created
    and disposed inside the loop avoids that.
    """
    task_engine = create_async_engine(normalize_async_url(settings.database_url), poolclass=NullPool)
    try:
        async with async_sessionmaker(task_engine, expire_on_commit=False, class_=AsyncSession)() as session:
            yield session
    finally:
        await task_engine.dispose()
