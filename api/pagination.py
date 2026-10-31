from __future__ import annotations

from dataclasses import dataclass

from fastapi import Query, Response


@dataclass(slots=True)
class Page:
    limit: int | None
    offset: int


def page_params(
    limit: int | None = Query(default=None, ge=1, le=500, description="Page size; omit for all rows"),
    offset: int = Query(default=0, ge=0),
) -> Page:
    return Page(limit=limit, offset=offset)


def set_total(response: Response, total: int) -> None:
    response.headers["X-Total-Count"] = str(total)
