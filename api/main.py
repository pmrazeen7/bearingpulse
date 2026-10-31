from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.routes import alerts, analytics, asins, crawl, sellers
from api.security import verify_api_key
from config.settings import get_settings
from db.database import get_db_session


settings = get_settings()
logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
    yield
    close = getattr(app.state.redis, "aclose", None) or app.state.redis.close
    result = close()
    if hasattr(result, "__await__"):
        await result


app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    lifespan=lifespan,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["X-API-Key", "Content-Type"],
    expose_headers=["X-Total-Count", "Content-Disposition"],
)


@app.middleware("http")
async def access_log(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info("%s %s -> %s (%.1f ms)", request.method, request.url.path, response.status_code, elapsed_ms)
    return response


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


protected = [Depends(verify_api_key)]
for module in (asins, sellers, analytics, alerts, crawl):
    app.include_router(module.router, prefix="/api", dependencies=protected)


async def _redis_status(request: Request) -> str:
    try:
        result = request.app.state.redis.ping()
        if hasattr(result, "__await__"):
            await result
        return "ok"
    except Exception as exc:
        logger.warning("Redis health check failed: %s", exc)
        return "unavailable"


@app.get("/api/health", tags=["system"])
async def health(request: Request, session: AsyncSession = Depends(get_db_session)):
    """Public liveness/readiness probe. Reports component status only, never configuration."""
    try:
        await session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as exc:
        logger.error("Database health check failed: %s", exc)
        db_status = "unavailable"
    redis_status = await _redis_status(request)
    overall = "ok" if db_status == "ok" and redis_status == "ok" else ("degraded" if db_status == "ok" else "down")
    body = {"status": overall, "db": db_status, "redis": redis_status, "version": app.version}
    return JSONResponse(status_code=200 if db_status == "ok" else 503, content=body)


@app.get("/api/auth/verify", tags=["system"], dependencies=protected)
async def verify_key():
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}
