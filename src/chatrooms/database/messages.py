"""Database queries for messages table."""

from datetime import datetime
from typing import Any, Literal

from psycopg import AsyncCursor
from psycopg.rows import class_row

from chatrooms import schemas
from chatrooms.database import common
from chatrooms.database.connections import DB

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS messages(
    id          SERIAL          PRIMARY KEY,
    room_id     INTEGER         NOT NULL,
    created_by  INTEGER         NOT NULL,
    content     TEXT            NOT NULL,
    created_at  TIMESTAMPTZ     NOT NULL
);
"""


ADD_TABLE_REFERENCES = """
ALTER TABLE messages
ADD CONSTRAINT messages_room_id_fkey FOREIGN KEY(room_id) REFERENCES rooms(id),
ADD CONSTRAINT messages_created_by_fkey FOREIGN KEY(created_by) REFERENCES users(id);
CREATE INDEX IF NOT EXISTS messages_room_id_index ON messages(room_id);
"""

TABLE = "messages"

COLUMNS = (
    "id",
    "room_id",
    "created_by",
    "content",
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


async def get_messages(
    db: DB,
    sort_by: str | None = None,
    sort_dir: Literal["asc", "desc"] = "asc",
    skip: int = 0,
    limit: int = 100,
) -> list[schemas.Message]:
    """Get messages."""
    async with db.cursor(row_factory=class_row(schemas.Message)) as cursor:
        await Q.select(cursor, sort_by=sort_by, sort_dir=sort_dir, limit=limit, skip=skip)
        return await cursor.fetchall()


async def get_messages_by_room_id(
    db: DB,
    room_id: int,
    sort_by: str | None = None,
    sort_dir: Literal["asc", "desc"] = "asc",
    skip: int = 0,
    limit: int = 100,
) -> list[schemas.Message]:
    """Get messages by room_id."""
    async with db.cursor(row_factory=class_row(schemas.Message)) as cursor:
        await Q.select(
            cursor, sort_by=sort_by, sort_dir=sort_dir, limit=limit, skip=skip, room_id=room_id
        )
        return await cursor.fetchall()


async def get_messages_by_created_by(
    db: DB,
    created_by: int,
    sort_by: str | None = None,
    sort_dir: Literal["asc", "desc"] = "asc",
    skip: int = 0,
    limit: int = 100,
) -> list[schemas.Message]:
    """Get messages by created_by."""
    async with db.cursor(row_factory=class_row(schemas.Message)) as cursor:
        await Q.select(
            cursor,
            sort_by=sort_by,
            sort_dir=sort_dir,
            limit=limit,
            skip=skip,
            created_by=created_by,
        )
        return await cursor.fetchall()


async def get_message_by_id(db: DB, message_id: int) -> schemas.Message | None:
    """Get message by id."""
    async with db.cursor(row_factory=class_row(schemas.Message)) as cursor:
        await Q.select(cursor, id=message_id)
        return await cursor.fetchone()


async def create_message(
    db: DB, message: schemas.MessageIn, created_by: int, created_at: datetime
) -> schemas.Message:
    """Create message."""
    async with db.cursor(row_factory=class_row(schemas.Message)) as cursor:
        await Q.insert(
            cursor,
            content=message.content,
            room_id=message.room_id,
            created_at=created_at,
            created_by=created_by,
        )
        doc = await cursor.fetchone()
        assert doc is not None, "Error while inserting"
        return doc


__all__ = (
    "add_table_references",
    "ADD_TABLE_REFERENCES",
    "create_message",
    "create_table",
    "CREATE_TABLE",
    "get_message_by_id",
    "get_messages_by_created_by",
    "get_messages",
)
