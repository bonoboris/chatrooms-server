"""Database queries for files table."""

from typing import Any, Literal

from psycopg import AsyncCursor
from psycopg.rows import class_row

from chatrooms import schemas
from chatrooms.database import common
from chatrooms.database.connections import DB

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS files(
    id              SERIAL          PRIMARY KEY,
    fs_filename     TEXT            NOT NULL,
    filename        TEXT            NOT NULL,
    content_type    TEXT            NOT NULL,
    size            INTEGER         NOT NULL,
    checksum        TEXT            NOT NULL,
    uploaded_at     TIMESTAMPTZ     NOT NULL,
    user_id         INTEGER         NOT NULL
);
"""

ADD_TABLE_REFERENCES = """
ALTER TABLE files
ADD CONSTRAINT files_user_id_fkey FOREIGN KEY(user_id) REFERENCES users(id);
"""


TABLE = "files"

COLUMNS = (
    "id",
    "fs_filename",
    "filename",
    "content_type",
    "size",
    "checksum",
    "uploaded_at",
    "user_id",
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


async def get_files(
    db: DB,
    sort_by: str | None = None,
    sort_dir: Literal["asc", "desc"] = "asc",
    skip: int = 0,
    limit: int = 100,
) -> list[schemas.FileDB]:
    """Get files."""
    async with db.cursor(row_factory=class_row(schemas.FileDB)) as cursor:
        await Q.select(cursor, sort_by=sort_by, sort_dir=sort_dir, limit=limit, skip=skip)
        return await cursor.fetchall()


async def get_files_by_user_id(
    db: DB,
    user_id: int,
    sort_by: str | None = None,
    sort_dir: Literal["asc", "desc"] = "asc",
    skip: int = 0,
    limit: int = 100,
) -> list[schemas.FileDB]:
    """Get files by user id."""
    async with db.cursor(row_factory=class_row(schemas.FileDB)) as cursor:
        await Q.select(
            cursor,
            sort_by=sort_by,
            sort_dir=sort_dir,
            limit=limit,
            skip=skip,
            user_id=user_id,
        )
        return await cursor.fetchall()


async def get_file_by_id(db: DB, file_id: int) -> schemas.FileDB | None:
    """Get file by id."""
    async with db.cursor(row_factory=class_row(schemas.FileDB)) as cursor:
        await Q.select(cursor, id=file_id)
        return await cursor.fetchone()


async def get_file_by_fs_filename(db: DB, fs_filename: str) -> schemas.FileDB | None:
    """Get file by fs_filename."""
    async with db.cursor(row_factory=class_row(schemas.FileDB)) as cursor:
        await Q.select(cursor, fs_filename=fs_filename)
        return await cursor.fetchone()


async def create_file(db: DB, file: schemas.File, user_id: int) -> schemas.FileDB:
    """Create file."""
    async with db.cursor(row_factory=class_row(schemas.FileDB)) as cursor:
        await Q.insert(cursor, **file.model_dump(), user_id=user_id)
        doc = await cursor.fetchone()
        assert doc is not None, "Error while inserting"
        return doc


async def delete_file(db: DB, file_id: int) -> int:
    """Delete file."""
    async with db.cursor(row_factory=class_row(schemas.FileDB)) as cursor:
        await Q.delete_by_id(cursor, id=file_id)
        return cursor.rowcount


__all__ = (
    "add_table_references",
    "ADD_TABLE_REFERENCES",
    "create_file",
    "create_table",
    "CREATE_TABLE",
    "get_file_by_fs_filename",
    "get_file_by_id",
    "get_files_by_user_id",
    "get_files",
)
