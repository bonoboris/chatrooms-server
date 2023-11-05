import functools
from datetime import datetime
from typing import Any, Callable, Generator

import psycopg
import psycopg.rows
from fastapi import FastAPI

from chatrooms import database, schemas
from chatrooms.auth import hash_password
from chatrooms.database.connections import DB
from chatrooms.settings import SettingsModel

DB_NAME = "test"


@functools.lru_cache
def get_testing_settings():
    return SettingsModel(
        pg_username="test",
        pg_password="test",
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
    async with db.cursor() as cursor:
        await cursor.execute(
            """
            DROP TABLE IF EXISTS messages;
            DROP TABLE IF EXISTS rooms;
            DROP TABLE IF EXISTS todos;
            DROP TABLE IF EXISTS users;
            DROP TABLE IF EXISTS files;
            """
        )
        await database.files.create_table(cursor)
        await database.users.create_table(cursor)
        await database.todos.create_table(cursor)
        await database.rooms.create_table(cursor)
        await database.messages.create_table(cursor)

        await database.files.add_table_references(cursor)
        await database.users.add_table_references(cursor)
        await database.todos.add_table_references(cursor)
        await database.rooms.add_table_references(cursor)
        await database.messages.add_table_references(cursor)
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
                ("user@example.com", "user", hash_password("pass"), True, now),
                ("another@example.com", "another", hash_password("ssap"), True, now),
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


# class AuthHeader(httpx.Auth):
#     requires_request_body = True

#     def __init__(self, username: str = "user", password: str = "pass", token: str | None = None):
#         self.username = username
#         self.password = password
#         self.token = token

#     @property
#     def credentials(self):
#         return {"username": self.username, "password": self.password}

#     def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
#         if self.token is not None:
#             request.headers["Authorization"] = self.token
#         response = yield request
#         if response.status_code == 401:
#             token = self.get_access_token(request)
#             print("TOKEN", token)
#             self.token = token
#             request.headers["Authorization"] = token
#             yield request

#     def get_access_token(self, request: httpx.Request) -> str:
#         """Send auth request, return token"""
#         print("REQUEST URL", request.url)
#         login_url = request.url.join("/login")
#         print("LOGIN_URL", login_url)
#         response = httpx.post(login_url, data=self.credentials)
#         response.raise_for_status()
#         data = response.json()
#         return data["token_type"] + " " + data["access_token"]
