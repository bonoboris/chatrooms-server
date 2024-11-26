"""Version 3 migration.

add `room_users` table
"""

from typing import Any

import psycopg

from chatrooms.database.migrations.migration_protocol import MigrationProtocol


class Version2(MigrationProtocol):
    """Version 3 migration.

    add `room_users` table
    """

    VERSION = 3

    @staticmethod
    async def _up(cursor: psycopg.AsyncCursor[dict[str, Any]]) -> None:
        await cursor.execute(
            """\
CREATE TABLE IF NOT EXISTS room_users(
    id          SERIAL          PRIMARY KEY,
    user_id     INTEGER         NOT NULL        REFERENCES users(id),
    room_id     INTEGER         NOT NULL        REFERENCES rooms(id),
    role        VARCHAR(255)    NOT NULL
);
"""
        )

    @staticmethod
    async def _down(cursor: psycopg.AsyncCursor[dict[str, Any]]) -> None:
        await cursor.execute("""DROP TABLE IF EXISTS room_users;""")
