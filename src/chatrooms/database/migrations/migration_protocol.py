"""Database migrations protocol and logic."""

import abc
import contextlib
import logging
from collections.abc import AsyncIterator
from typing import Any, Self

import psycopg

from chatrooms.database.connections import get_db_connection
from chatrooms.database.migrations.errors import MissingMigrationVersionError
from chatrooms.settings import get_settings

DB = psycopg.AsyncConnection[dict[str, Any]]

LOGGER = logging.getLogger("migrations")


@contextlib.asynccontextmanager
async def or_default_db(db: DB | None) -> AsyncIterator[DB]:
    """Get a database connection, or use the one provided."""
    if db is None:
        async with await get_db_connection(get_settings()) as conn:
            yield conn
    else:
        yield db


class MigrationProtocol(abc.ABC):
    """Migration protocol."""

    VERSION: int

    @classmethod
    async def up(cls: type[Self], db: DB | None = None) -> bool:
        """Up migration."""
        if not hasattr(cls, "VERSION"):
            raise MissingMigrationVersionError
        LOGGER.info(f"Up migration to version {cls.VERSION}")
        async with or_default_db(db) as db, db.cursor() as cursor:
            version = await cls._get_version(cursor)
            if version == cls.VERSION - 1:
                await cls._up(cursor)
                await cls._set_version(cursor, version=cls.VERSION)
                LOGGER.info(f"Done; version={cls.VERSION}")
                return True
            LOGGER.warning(f"Skipped: invalid current version {version}")
            return False

    @staticmethod
    @abc.abstractmethod
    async def _up(cursor: psycopg.AsyncCursor[dict[str, Any]]) -> None:
        ...

    @classmethod
    async def down(cls: type[Self], db: DB | None = None) -> bool:
        """Down migration."""
        if not hasattr(cls, "VERSION"):
            raise MissingMigrationVersionError
        LOGGER.info(f"Down migration from version {cls.VERSION}")
        async with or_default_db(db) as db, db.cursor() as cursor:
            version = await cls._get_version(cursor)
            if version == cls.VERSION:
                await cls._down(cursor)
                await cls._set_version(cursor, version=cls.VERSION - 1)
                LOGGER.info(f"Done: version={cls.VERSION - 1}")
                return True
            LOGGER.warning(f"Skipped: invalid current version {version}")
            return False

    @staticmethod
    @abc.abstractmethod
    async def _down(cursor: psycopg.AsyncCursor[dict[str, Any]]) -> None:
        ...

    @classmethod
    async def get_version(cls: type[Self], db: DB | None = None) -> int:
        """Get database version, if not existing return 0."""
        async with or_default_db(db) as db, db.cursor() as cursor:
            return await cls._get_version(cursor)

    @staticmethod
    async def _get_version(cursor: psycopg.AsyncCursor[dict[str, Any]]) -> int:
        """Get database version, if not existing return 0."""
        await cursor.execute(
            """SELECT EXISTS (
                SELECT 1
                FROM pg_tables
                WHERE tablename = 'version' AND schemaname = 'public'
            );"""
        )
        row = await cursor.fetchone()
        if row is None or not row["exists"]:
            return 0

        await cursor.execute("""SELECT version FROM version;""")
        row = await cursor.fetchone()
        if row is None:
            return 0
        return row["version"]

    @staticmethod
    async def _set_version(cursor: psycopg.AsyncCursor[dict[str, Any]], version: int) -> None:
        """Set database version to `cls.VERSION`."""
        await cursor.execute("""UPDATE version SET version = %(version)s;""", {"version": version})
