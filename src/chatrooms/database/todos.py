"""Database queries for todos table."""

from datetime import datetime
from typing import Any, Literal

from psycopg import AsyncCursor
from psycopg.rows import class_row

from chatrooms import schemas
from chatrooms.database import common
from chatrooms.database.connections import DB

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS todos(
    id          SERIAL          PRIMARY KEY,
    status      VARCHAR(255)    NOT NULL,
    description TEXT,
    created_at  TIMESTAMPTZ     NOT NULL,
    created_by  INTEGER         NOT NULL,
    modified_at TIMESTAMPTZ     NOT NULL

)
"""

ADD_TABLE_REFERENCES = """
ALTER TABLE todos
ADD CONSTRAINT todos_created_by_fkey FOREIGN KEY(created_by) REFERENCES users(id);
"""

TABLE = "todos"

COLUMNS = (
    "id",
    "status",
    "description",
    "created_at",
    "created_by",
    "modified_at",
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


async def get_todos(
    db: DB,
    sort_by: str | None = None,
    sort_dir: Literal["asc", "desc"] = "asc",
    skip: int = 0,
    limit: int = 100,
) -> list[schemas.Todo]:
    """Get todos."""
    async with db.cursor(row_factory=class_row(schemas.Todo)) as cursor:
        await Q.select(cursor, limit=limit, skip=skip, sort_by=sort_by, sort_dir=sort_dir)
        return await cursor.fetchall()


async def get_todos_by_created_by(
    db: DB,
    created_by: int,
    sort_by: str | None = None,
    sort_dir: Literal["asc", "desc"] = "asc",
    skip: int = 0,
    limit: int = 100,
) -> list[schemas.Todo]:
    """Get todos by created_by."""
    async with db.cursor(row_factory=class_row(schemas.Todo)) as cursor:
        await Q.select(
            cursor,
            limit=limit,
            skip=skip,
            sort_by=sort_by,
            sort_dir=sort_dir,
            created_by=created_by,
        )
        return await cursor.fetchall()


async def get_todo_by_id(db: DB, todo_id: int) -> schemas.Todo | None:
    """Get todo by id."""
    async with db.cursor(row_factory=class_row(schemas.Todo)) as cursor:
        await Q.select(cursor, id=todo_id)
        return await cursor.fetchone()


async def create_todo(
    db: DB, todo: schemas.TodoIn, created_by: int, created_at: datetime, modified_at: datetime
) -> schemas.Todo:
    """Create todo."""
    async with db.cursor(row_factory=class_row(schemas.Todo)) as cursor:
        await Q.insert(
            cursor,
            status=todo.status,
            description=todo.description,
            created_at=created_at,
            created_by=created_by,
            modified_at=modified_at,
        )
        record = await cursor.fetchone()
        assert record is not None, "Error while inserting"
        return record


async def update_todo(
    db: DB, todo_id: int, todo: schemas.TodoIn, modified_at: datetime
) -> schemas.Todo:
    """Update todo."""
    async with db.cursor(row_factory=class_row(schemas.Todo)) as cursor:
        await Q.update_by_id(
            cursor,
            id=todo_id,
            status=todo.status,
            description=todo.description,
            modified_at=modified_at,
        )
        row = await cursor.fetchone()
        assert row is not None, "Error while updating"
        return row


async def delete_todo(db: DB, todo_id: int) -> int:
    """Delete todo."""
    async with db.cursor(row_factory=class_row(schemas.Todo)) as cursor:
        await Q.delete_by_id(cursor, id=todo_id)
        return cursor.rowcount


__all__ = (
    "add_table_references",
    "ADD_TABLE_REFERENCES",
    "create_todo",
    "create_table",
    "CREATE_TABLE",
    "get_todo_by_id",
    "get_todos_by_created_by",
    "get_todos",
)
