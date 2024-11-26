import functools
from collections.abc import Callable, Generator
from datetime import datetime
from typing import Any

import psycopg
import psycopg.rows
from fastapi import FastAPI

from chatrooms import auth, schemas
from chatrooms.database import DB
from chatrooms.database.connections import get_db_connection
from chatrooms.database.migrations import core as migrations_core
from chatrooms.settings import SettingsModel

DB_NAME = "chatrooms_test"


@functools.lru_cache
def get_testing_settings() -> SettingsModel:
    return SettingsModel(pg_database=DB_NAME)


def reset_database() -> None:
    """Drop and recreate the test database."""
    settings = get_testing_settings()
    with psycopg.Connection[dict[str, Any]].connect(
        user=settings.pg_user,
        password=settings.pg_password.get_secret_value(),
        host=settings.pg_host,
        dbname="postgres",
        row_factory=psycopg.rows.dict_row,
        autocommit=True,
    ) as conn:
        conn.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
        conn.execute(f"CREATE DATABASE {DB_NAME}")


async def reset_tables(db: DB) -> None:
    """Recreate the tables in the test database."""
    for migration in reversed(migrations_core.MIGRATIONS):
        await migration.down(db)
    for migration in migrations_core.MIGRATIONS:
        await migration.up(db)
    await db.commit()


async def reset_db() -> DB:
    """Reset the test database, recreate the tables, and return a connection."""
    reset_database()
    conn = await get_db_connection(get_testing_settings())
    await reset_tables(conn)
    return conn


async def add_users(db: DB) -> None:
    """Add test users ('user' and 'another') to the database."""
    async with db.cursor() as cursor:
        now = datetime.now().astimezone()
        await cursor.executemany(
            """
            INSERT INTO users (email, username, digest, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            [
                ("user@example.com", "user", auth.hash_password("pass"), True, now),
                ("another@example.com", "another", auth.hash_password("ssap"), True, now),
            ],
        )
    await db.commit()


async def get_user_no_auth(db: DB) -> schemas.UserDB:
    """Dependency override for user/auth; returns an authenticated user named 'user'."""
    cur = await db.execute("SELECT * FROM users WHERE username = 'user'")
    user = await cur.fetchone()
    assert user is not None, "Cannot find test user (username='user') in database"
    return schemas.UserDB.model_validate(user)


async def get_another_user(db: DB) -> schemas.UserDB:
    """Dependency override for user/auth; returns an authenticated user named 'another'."""
    cur = await db.execute(
        "SELECT * FROM users WHERE username = 'another'",
    )
    user = await cur.fetchone()
    assert user is not None, "Cannot find test user (username='another') in database"
    return schemas.UserDB.model_validate(user)


def with_overrides(
    app: FastAPI, overrides: dict[Callable[..., Any], Callable[..., Any]]
) -> Generator[FastAPI, Any, Any]:
    """Override dependencies in the FastAPI app, reset dependencies as cleanup."""
    prevs: dict[Callable[..., Any], Callable[..., Any]] = {}
    for key, value in overrides.items():
        if key in app.dependency_overrides:
            prevs[key] = app.dependency_overrides[key]
        app.dependency_overrides[key] = value
    yield app
    for key in overrides:
        if key in app.dependency_overrides:
            del app.dependency_overrides[key]
            if key in prevs:
                app.dependency_overrides[key] = prevs[key]
