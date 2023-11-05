"""Database migrations scripts."""

import abc
import contextlib
import logging
from collections.abc import AsyncIterator
from typing import Any

import psycopg

from chatrooms.database.connections import get_db_connection
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
    async def up(cls, db: DB | None = None) -> None:
        """Up migration."""
        assert hasattr(cls, "VERSION"), "Migration must have a VERSION class attribute."
        LOGGER.info(f"Up migration to version {cls.VERSION}")
        async with or_default_db(db) as db, db.cursor() as cursor:
            version = await cls.get_version(cursor)
            if version == cls.VERSION - 1:
                await cls._up(cursor)
                await cls.set_version(cursor, version=cls.VERSION)
                LOGGER.info(f"Done; version={cls.VERSION}")
            else:
                LOGGER.warning(f"Skipped: invalid current version {version}")

    @staticmethod
    @abc.abstractmethod
    async def _up(cursor: psycopg.AsyncCursor[dict[str, Any]]) -> None:
        ...

    @classmethod
    async def down(cls, db: DB | None = None) -> None:
        """Down migration."""
        assert hasattr(cls, "VERSION"), "Migration must have a VERSION class attribute."
        LOGGER.info(f"Down migration from version {cls.VERSION}")
        async with or_default_db(db) as db, db.cursor() as cursor:
            version = await cls.get_version(cursor)
            if version == cls.VERSION:
                await cls._down(cursor)
                await cls.set_version(cursor, version=cls.VERSION - 1)
                LOGGER.info(f"Done: version={cls.VERSION - 1}")
            else:
                LOGGER.warning(f"Skipped: invalid current version {version}")

    @staticmethod
    @abc.abstractmethod
    async def _down(cursor: psycopg.AsyncCursor[dict[str, Any]]) -> None:
        ...

    @staticmethod
    async def get_version(cursor: psycopg.AsyncCursor[dict[str, Any]]) -> int:
        """Get database version, if not existing return 0."""
        await cursor.execute("""SELECT version FROM version;""")
        row = await cursor.fetchone()
        if row is None:
            return 0
        return row["version"]

    @staticmethod
    async def set_version(cursor: psycopg.AsyncCursor[dict[str, Any]], version: int) -> None:
        """Set database version to `cls.VERSION`."""
        await cursor.execute("""UPDATE version SET version = %(version)s;""", {"version": version})


class Version1(MigrationProtocol):
    """Version 1 migration.

    Create tables.
    """

    VERSION = 1

    @staticmethod
    async def _up(cursor: psycopg.AsyncCursor[dict[str, Any]]) -> None:
        await cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS users(
                    id          SERIAL          PRIMARY KEY,
                    email       VARCHAR(255)    NOT NULL,
                    username    VARCHAR(255)    NOT NULL,
                    digest      VARCHAR(255)    NOT NULL,
                    is_active   BOOLEAN         NOT NULL,
                    created_at  TIMESTAMPTZ     NOT NULL,
                    avatar_id   INTEGER
                );
                CREATE TABLE IF NOT EXISTS files(
                    id              SERIAL          PRIMARY KEY,
                    fs_filename     TEXT            NOT NULL,
                    filename        TEXT            NOT NULL,
                    content_type    TEXT            NOT NULL,
                    size            INTEGER         NOT NULL,
                    checksum        TEXT            NOT NULL,
                    uploaded_at     TIMESTAMPTZ     NOT NULL,
                    user_id         INTEGER         NOT NULL        REFERENCES users(id)
                );

                ALTER TABLE users
                ADD CONSTRAINT users_avatar_id_fkey FOREIGN KEY(avatar_id) REFERENCES files(id);

                CREATE TABLE IF NOT EXISTS todos(
                    id          SERIAL          PRIMARY KEY,
                    status      VARCHAR(255)    NOT NULL,
                    description TEXT            NOT NULL,
                    created_at  TIMESTAMPTZ     NOT NULL,
                    created_by  INTEGER         NOT NULL        REFERENCES users(id),
                    modified_at TIMESTAMPTZ     NOT NULL
                );
                CREATE TABLE IF NOT EXISTS rooms(
                    id          SERIAL          PRIMARY KEY,
                    name        VARCHAR(255)    NOT NULL UNIQUE,
                    created_by  INTEGER         NOT NULL        REFERENCES users(id),
                    created_at  TIMESTAMPTZ     NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages(
                    id          SERIAL          PRIMARY KEY,
                    content     TEXT            NOT NULL,
                    room_id     INTEGER         NOT NULL        REFERENCES rooms(id),
                    created_by  INTEGER         NOT NULL        REFERENCES users(id),
                    created_at  TIMESTAMPTZ     NOT NULL
                );
                CREATE TABLE IF NOT EXISTS version(
                    id          SERIAL          PRIMARY KEY,
                    version     INTEGER         NOT NULL
                );
                INSERT INTO version(version) VALUES(1);
                """
        )

    @staticmethod
    async def _down(cursor: psycopg.AsyncCursor[dict[str, Any]]) -> None:
        """Create tables."""
        await cursor.execute("""SELECT version FROM version;""")
        row = await cursor.fetchone()
        if row is not None:
            return
        await cursor.execute(
            """
            DROP TABLE IF EXISTS messages;
            DROP TABLE IF EXISTS rooms;
            DROP TABLE IF EXISTS users;
            DROP TABLE IF EXISTS todos;
            DROP TABLE IF EXISTS files;
            """
        )


MIGRATIONS: tuple[type[MigrationProtocol], ...] = (Version1,)


async def all_up(db: DB | None) -> None:
    """Run all up migrations."""
    for migration in MIGRATIONS:
        await migration.up(db)


async def all_down(db: DB | None) -> None:
    """Run all down migrations."""
    for migration in reversed(MIGRATIONS):
        await migration.down(db)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  [%(levelname)-10s] %(message)-60s [%(name)-10s]",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    import asyncio

    asyncio.run(Version1.up())
