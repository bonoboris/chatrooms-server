"""Database queries for rooms table."""

from datetime import datetime
from typing import Any, Literal

from psycopg import AsyncCursor
from psycopg.rows import class_row

from chatrooms import schemas
from chatrooms.database import common
from chatrooms.database.connections import DB

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS rooms(
    id          SERIAL          PRIMARY KEY,
    name        VARCHAR(255)    UNIQUE NOT NULL,
    created_by  INTEGER         NOT NULL,
    created_at  TIMESTAMPTZ     NOT NULL
);
"""

ADD_TABLE_REFERENCES = """
ALTER TABLE rooms
ADD CONTRAINT rooms_created_by_fkey FOREIGN KEY(created_by) REFERENCES users(id);
"""


TABLE = "rooms"

COLUMNS = (
    "id",
    "name",
    "created_by",
    "created_at",
)

Q = common.Querier(TABLE, COLUMNS)


async def create_table(
    db_or_cursor: DB | AsyncCursor[dict[str, Any]]
) -> AsyncCursor[dict[str, Any]]:
    """Create table, without constraint."""
    return await db_or_cursor.execute(CREATE_TABLE)


async def add_table_references(
    db_or_cursor: DB | AsyncCursor[dict[str, Any]]
) -> AsyncCursor[dict[str, Any]]:
    """Create foreign constraints."""
    return await db_or_cursor.execute(ADD_TABLE_REFERENCES)


async def get_rooms(
    db: DB,
    sort_by: str | None = None,
    sort_dir: Literal["asc", "desc"] = "asc",
    skip: int = 0,
    limit: int = 100,
) -> list[schemas.Room]:
    """Get rooms."""
    async with db.cursor(row_factory=class_row(schemas.Room)) as cursor:
        await Q.select(cursor, sort_by=sort_by, sort_dir=sort_dir, limit=limit, skip=skip)
        return await cursor.fetchall()


async def get_rooms_by_created_by(
    db: DB,
    created_by: int,
    sort_by: str | None = None,
    sort_dir: Literal["asc", "desc"] = "asc",
    skip: int = 0,
    limit: int = 100,
) -> list[schemas.Room]:
    """Get rooms by created_by."""
    async with db.cursor(row_factory=class_row(schemas.Room)) as cursor:
        await Q.select(
            cursor,
            sort_by=sort_by,
            sort_dir=sort_dir,
            limit=limit,
            skip=skip,
            created_by=created_by,
        )
        return await cursor.fetchall()


async def get_room_by_id(db: DB, room_id: int) -> schemas.Room | None:
    """Get room by id."""
    async with db.cursor(row_factory=class_row(schemas.Room)) as cursor:
        await Q.select(cursor, id=room_id)
        return await cursor.fetchone()


async def get_room_by_name(db: DB, room_name: str) -> schemas.Room | None:
    """Get room by name."""
    async with db.cursor(row_factory=class_row(schemas.Room)) as cursor:
        await Q.select(cursor, name=room_name)
        return await cursor.fetchone()


async def create_room(
    db: DB, room: schemas.RoomIn, created_by: int, created_at: datetime
) -> schemas.Room:
    """Create room."""
    async with db.cursor(row_factory=class_row(schemas.Room)) as cursor:
        await Q.insert(cursor, name=room.name, created_at=created_at, created_by=created_by)
        room_db = await cursor.fetchone()
        assert room_db is not None, "Error while inserting"
        return room_db


__all__ = (
    "add_table_references",
    "ADD_TABLE_REFERENCES",
    "create_room",
    "create_table",
    "CREATE_TABLE",
    "get_room_by_id",
    "get_rooms_by_created_by",
    "get_rooms",
)
