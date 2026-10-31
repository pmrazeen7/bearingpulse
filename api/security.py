from __future__ import annotations

import hmac

from fastapi import Header, HTTPException, status

from config.settings import get_settings


async def verify_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    expected = get_settings().api_key
    if not x_api_key or not hmac.compare_digest(x_api_key.encode(), expected.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key",
            headers={"WWW-Authenticate": "APIKey"},
        )
