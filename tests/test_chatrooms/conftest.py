import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
import uvloop
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatrooms import app as m_app
from chatrooms.auth import (
    get_current_active_user,
    get_current_active_user_from_websocket,
    get_current_user,
    get_current_user_from_websocket,
)
from chatrooms.database.connections import DB
from chatrooms.settings import get_settings

from .common import (
    add_users,
    get_another_user,
    get_testing_settings,
    get_user_no_auth,
    reset_db,
    with_overrides,
)


@pytest.fixture(scope="session")
def event_loop():
    """Session scope uvloop as event loop."""
    loop = uvloop.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def app() -> FastAPI:
    """Create a FastAPI app with testing settings."""
    app = m_app.create_app()
    app.dependency_overrides[get_settings] = get_testing_settings
    return app


@pytest.fixture(scope="session")
def client(app: FastAPI) -> TestClient:
    """Create a TestClient for the FastAPI app."""
    return TestClient(app)


USER_DEPS = (
    get_current_user,
    get_current_active_user,
    get_current_user_from_websocket,
    get_current_active_user_from_websocket,
)


@pytest.fixture(scope="module")
async def empty_db() -> AsyncGenerator[DB, None]:
    """Reset the test database and return a connection."""
    db = await reset_db()
    yield db
    await db.close()


@pytest.fixture(scope="module")
async def db(empty_db: DB) -> DB:
    """Reset the test database, adds testusers, and return a connection."""
    await add_users(empty_db)
    return empty_db


@pytest.fixture(scope="module")
def user_app(app: FastAPI) -> Generator[FastAPI, Any, Any]:
    """Override user dependencies with the authenticated user 'user'."""
    app.dependency_overrides[get_settings] = get_testing_settings
    overrides = {k: get_user_no_auth for k in USER_DEPS}
    yield from with_overrides(app, overrides)


@pytest.fixture()
def another_user_app(app: FastAPI) -> Generator[FastAPI, Any, Any]:
    """Override user dependencies with the authenticated user 'another'."""
    app.dependency_overrides[get_settings] = get_testing_settings
    overrides = {k: get_another_user for k in USER_DEPS}
    yield from with_overrides(app, overrides)
