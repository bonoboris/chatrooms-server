"""Migration actions."""

import logging

from chatrooms.database.connections import get_db_connection
from chatrooms.database.migrations import version1, version2
from chatrooms.database.migrations.migration_protocol import DB, MigrationProtocol
from chatrooms.settings import Settings, get_settings

MIGRATIONS: tuple[type[MigrationProtocol], ...] = (version1.Version1, version2.Version2)
LOGGER = logging.getLogger("migrations")


async def get_version(settings: Settings | None) -> int:
    """Get database current version."""
    settings = get_settings()
    async with await get_db_connection(settings) as db:
        return await MigrationProtocol.get_version(db)


async def one_up(settings: Settings | None) -> bool:
    """Run one up migration."""
    settings = get_settings()
    async with await get_db_connection(settings) as db:
        current_version = await MigrationProtocol.get_version(db)
        if current_version >= len(MIGRATIONS):
            LOGGER.info("Current version is up to date")
            return False
        await MIGRATIONS[current_version].up(db)
        return True


async def one_down(settings: Settings | None) -> bool:
    """Run one down migration."""
    settings = get_settings()
    async with await get_db_connection(settings) as db:
        current_version = await MigrationProtocol.get_version(db)
        if current_version == 1:
            LOGGER.info("Current version is 1")
            return False
        await MIGRATIONS[current_version - 1].down(db)
        return True


async def all_up(db: DB | None) -> None:
    """Run all up migrations."""
    for migration in MIGRATIONS:
        await migration.up(db)


async def all_down(db: DB | None) -> None:
    """Run all down migrations."""
    for migration in reversed(MIGRATIONS):
        await migration.down(db)
