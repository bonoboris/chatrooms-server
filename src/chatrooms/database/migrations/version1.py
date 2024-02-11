"""Version 1 migration.

Create tables.
"""
from typing import Any

import psycopg

from chatrooms.database.migrations.migration_protocol import MigrationProtocol


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
