"""Database queries for users table."""

from datetime import datetime
from typing import Any

from psycopg import AsyncCursor
from psycopg.rows import class_row

from chatrooms import schemas
from chatrooms.database import common
from chatrooms.database.connections import DB

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS users(
    id          SERIAL          PRIMARY KEY,
    email       VARCHAR(255)    NOT NULL,
    username    VARCHAR(255)    NOT NULL,
    digest      VARCHAR(255)    NOT NULL,
    is_active   BOOLEAN         NOT NULL,
    created_at  TIMESTAMPTZ     NOT NULL,
    avatar_id   INTEGER
);
"""


ADD_TABLE_REFERENCES = """
ALTER TABLE users
ADD CONSTRAINT users_avatar_id_fkey FOREIGN KEY(avatar_id) REFERENCES files(id);
"""


TABLE = "users"

COLUMNS = (
    "id",
    "email",
    "username",
    "digest",
    "is_active",
    "created_at",
    "avatar_id",
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


async def get_user_by_id(db: DB, user_id: int) -> schemas.UserDB | None:
    """Get user by id."""
    async with db.cursor(row_factory=class_row(schemas.UserDB)) as cursor:
        await Q.select(cursor, id=user_id)
        return await cursor.fetchone()


async def get_user_by_email(db: DB, email: str) -> schemas.UserDB | None:
    """Get user by email."""
    async with db.cursor(row_factory=class_row(schemas.UserDB)) as cursor:
        await Q.select(cursor, email=email)
        return await cursor.fetchone()


async def get_user_by_username(db: DB, username: str) -> schemas.UserDB | None:
    """Get user by username."""
    async with db.cursor(row_factory=class_row(schemas.UserDB)) as cursor:
        await Q.select(cursor, username=username)
        return await cursor.fetchone()


async def get_users(db: DB, skip: int = 0, limit: int = 100) -> list[schemas.UserDB]:
    """Get users."""
    async with db.cursor(row_factory=class_row(schemas.UserDB)) as cursor:
        await Q.select(cursor, limit=limit, skip=skip)
        return await cursor.fetchall()


async def create_user(
    db: DB,
    user: schemas.UserIn,
    digest: str,
    created_at: datetime,
    avatar_id: int | None = None,
    *,
    is_active: bool = True,
) -> schemas.UserDB:
    """Create user."""
    async with db.cursor(row_factory=class_row(schemas.UserDB)) as cursor:
        await Q.insert(
            cursor,
            email=user.email,
            username=user.username,
            digest=digest,
            is_active=is_active,
            created_at=created_at,
            avatar_id=avatar_id,
        )
        record = await cursor.fetchone()
        assert record is not None, "Error while inserting"
        return record


async def update_user(db: DB, user_id: int, user: schemas.UserIn) -> schemas.UserDB:
    """Update user."""
    async with db.cursor(row_factory=class_row(schemas.UserDB)) as cursor:
        await Q.update_by_id(cursor, id=user_id, **user.model_dump())
        row = await cursor.fetchone()
        assert row is not None, "Error while updating"
        return row


async def update_user_avatar(db: DB, user_id: int, avatar_id: int) -> schemas.UserDB:
    """Update user avatar_id."""
    async with db.cursor(row_factory=class_row(schemas.UserDB)) as cursor:
        await Q.update_by_id(cursor, id=user_id, avatar_id=avatar_id)
        row = await cursor.fetchone()
        assert row is not None, "Error while updating"
        return row


__all__ = (
    "add_table_references",
    "ADD_TABLE_REFERENCES",
    "create_user",
    "create_table",
    "CREATE_TABLE",
    "get_user_by_email",
    "get_user_by_id",
    "get_user_by_username",
    "get_users",
)
