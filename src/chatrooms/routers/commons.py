"""Commons for routers."""

import datetime
from typing import Annotated, Any, Literal

import pydantic
from fastapi import Depends


class DeleteStatus(pydantic.BaseModel):
    """Delete status."""

    status: Literal["deleted", "not found"]


class DefaultErrorResponse(pydantic.BaseModel):
    """Default response schema for http errors."""

    detail: str | None


class PaginationParams(pydantic.BaseModel):
    """PaginationParams."""

    skip: int = 0
    limit: int = 100
    sort_by: str | None = None
    sort_dir: Literal["asc", "desc"] = "asc"


Pagination = Annotated[PaginationParams, Depends()]


def default_errors(*codes: int) -> dict[int | str, dict[str, Any]]:
    """A `responses` value for http codes with the `DefaultErrorResponse` model."""
    return {code: {"model": DefaultErrorResponse} for code in codes}


def utcnow() -> datetime.datetime:
    """Now in UTC timezone."""
    return datetime.datetime.now().astimezone(datetime.UTC)
