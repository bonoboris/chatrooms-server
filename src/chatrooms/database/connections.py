"""DB connections."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated, Any

import psycopg
import psycopg.rows
from fastapi import Depends

from chatrooms.settings import Settings


async def get_db_connection(settings: Settings) -> psycopg.AsyncConnection[dict[str, Any]]:
    """Get a database connection."""
    return await psycopg.AsyncConnection.connect(
        user=settings.pg_username,
        password=settings.pg_password,
        host=settings.pg_host,
        dbname=settings.pg_database,
        row_factory=psycopg.rows.dict_row,
    )


async def _get_db_connection(
    settings: Settings
) -> AsyncGenerator[psycopg.AsyncConnection[dict[str, Any]], None]:
    """Create, enter and yield a database connection."""
    async with await get_db_connection(settings) as conn:
        yield conn


DB = Annotated[psycopg.AsyncConnection[dict[str, Any]], Depends(_get_db_connection)]

__all__ = (
    "DB",
    "get_db_connection",
)
