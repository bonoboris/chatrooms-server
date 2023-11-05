import asyncio
from typing import Any, Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatrooms import app as m_app
from chatrooms.auth import (
    get_current_active_user,
    get_current_active_user_from_websocket,
    get_current_user,
    get_current_user_from_websocket,
)
from chatrooms.database.connections import DB, get_db_connection
from chatrooms.settings import get_settings

from .common import (
    add_users,
    get_another_user,
    get_testing_settings,
    get_user_no_auth,
    reset_database,
    reset_tables,
    with_overrides,
)


@pytest.fixture(scope="session")
def event_loop():
    event_loop = asyncio.get_event_loop()
    yield event_loop
    event_loop.close()


@pytest.fixture(scope="session")
def app() -> FastAPI:
    app = m_app.create_app()
    app.dependency_overrides[get_settings] = get_testing_settings
    return app


@pytest.fixture(scope="session")
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


USER_DEPS = (
    get_current_user,
    get_current_active_user,
    get_current_user_from_websocket,
    get_current_active_user_from_websocket,
)


@pytest.fixture(scope="function")
def user_app(app: FastAPI) -> Generator[FastAPI, Any, Any]:
    app.dependency_overrides[get_settings] = get_testing_settings
    overrides = {k: get_user_no_auth for k in USER_DEPS}
    yield from with_overrides(app, overrides)


@pytest.fixture(scope="function")
def another_user_app(app: FastAPI) -> Generator[FastAPI, Any, Any]:
    app.dependency_overrides[get_settings] = get_testing_settings
    overrides = {k: get_another_user for k in USER_DEPS}
    yield from with_overrides(app, overrides)


@pytest.fixture(scope="module", autouse=True)
async def empty_db() -> DB:
    reset_database()
    conn = await get_db_connection(get_testing_settings())
    await reset_tables(conn)
    return conn


@pytest.fixture(scope="module")
async def db(empty_db: DB) -> DB:
    await add_users(empty_db)
    return empty_db
