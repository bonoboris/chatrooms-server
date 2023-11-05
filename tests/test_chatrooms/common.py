import functools
from collections.abc import Callable, Generator
from datetime import datetime
from typing import Any

import psycopg
import psycopg.rows
from chatrooms import auth, schemas
from chatrooms.database import DB, migrations
from chatrooms.settings import SettingsModel
from fastapi import FastAPI

DB_NAME = "test"


@functools.lru_cache
def get_testing_settings():
    return SettingsModel(
        pg_username="test",
        pg_password="test",  # noqa: S106
        pg_database=DB_NAME,
    )


def reset_database():
    settings = get_testing_settings()
    conn = psycopg.Connection.connect(
        user=settings.pg_username,
        password=settings.pg_password,
        host=settings.pg_host,
        dbname="postgres",
        row_factory=psycopg.rows.dict_row,
        autocommit=True,
    )
    conn.execute("DROP DATABASE TEST")
    conn.execute("CREATE DATABASE TEST")


async def reset_tables(db: DB):
    await migrations.all_down(db)
    await migrations.all_up(db)
    await db.commit()


async def add_users(db: DB):
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
    cur = await db.execute("SELECT * FROM users WHERE username = 'user'")
    user = await cur.fetchone()
    assert user is not None, "Cannot find test user (username='user') in database"
    return schemas.UserDB.model_validate(user)


async def get_another_user(db: DB) -> schemas.UserDB:
    cur = await db.execute(
        "SELECT * FROM users WHERE username = 'another'",
    )
    user = await cur.fetchone()
    assert user is not None, "Cannot find test user (username='another') in database"
    return schemas.UserDB.model_validate(user)


def with_overrides(
    app: FastAPI, overrides: dict[Callable[..., Any], Callable[..., Any]]
) -> Generator[FastAPI, Any, Any]:
    prevs: dict[Callable[..., Any], Callable[..., Any]] = {}
    for key, value in overrides.items():
        if key in app.dependency_overrides:
            prevs[key] = app.dependency_overrides[key]
        app.dependency_overrides[key] = value
    yield app
    for key in overrides:
        del app.dependency_overrides[key]
        if key in prevs:
            app.dependency_overrides[key] = prevs[key]
