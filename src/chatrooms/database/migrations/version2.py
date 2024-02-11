"""Version 2 migration.

files table:
    - add `fs_folder` field and update with folder part of `fs_filename` field
    - remove folder part from `fs_filename` field
"""

from typing import Any

import psycopg

from chatrooms.database.migrations.migration_protocol import MigrationProtocol


class Version2(MigrationProtocol):
    """Version 2 migration.

    files table:
        - add `fs_folder` field and update with folder part of `fs_filename` field
        - remove folder part from `fs_filename` field
    """

    VERSION = 2

    @staticmethod
    async def _up(cursor: psycopg.AsyncCursor[dict[str, Any]]) -> None:
        await cursor.execute("""ALTER TABLE files ADD COLUMN fs_folder VARCHAR(255) NULL;""")
        await cursor.execute("""SELECT id, fs_filename FROM files;""")
        rows = await cursor.fetchall()
        updates: list[dict[str, Any]] = []

        for row in rows:
            fs_folder, fs_filename = row["fs_filename"].split("/", 1)
            updates.append({"id": row["id"], "fs_folder": fs_folder, "fs_filename": fs_filename})
        await cursor.executemany(
            """
                UPDATE files
                SET fs_folder = %(fs_folder)s, fs_filename = %(fs_filename)s
                WHERE id = %(id)s;
                """,
            updates,
        )
        await cursor.execute("""ALTER TABLE files ALTER COLUMN fs_folder SET NOT NULL;""")

    @staticmethod
    async def _down(cursor: psycopg.AsyncCursor[dict[str, Any]]) -> None:
        await cursor.execute(
            """
                SELECT id, fs_folder, fs_filename FROM files;
                """
        )
        rows = await cursor.fetchall()
        updates: list[dict[str, Any]] = []
        for row in rows:
            fs_filename = "/".join((row["fs_folder"], row["fs_filename"]))
            updates.append({"id": row["id"], "fs_filename": fs_filename})
        await cursor.executemany(
            """
                UPDATE files
                SET fs_filename = %(fs_filename)s
                WHERE id = %(id)s;
                """,
            updates,
        )
        await cursor.execute(
            """
                ALTER TABLE files
                DROP COLUMN fs_folder;
                """
        )
