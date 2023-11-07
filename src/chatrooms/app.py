"""Main app file."""

import contextlib
from collections.abc import AsyncIterator

import fastapi
from fastapi.middleware.cors import CORSMiddleware

from chatrooms import DB_VERSION, VERSION, routers
from chatrooms.database import migrations


class DatabaseVersionError(RuntimeError):
    """Database version & API version mismatch."""

    def __init__(self, expected: int, got: int) -> None:
        super().__init__(f"Database version & API version mismatch: expected={expected}, got={got}")
        self.expected = expected
        self.got = got


@contextlib.asynccontextmanager
async def lifespan(_app: fastapi.FastAPI) -> AsyncIterator[None]:
    """Run startup and shutdown events."""
    db_version = await migrations.MigrationProtocol.get_version()
    if db_version != DB_VERSION:
        raise DatabaseVersionError(expected=DB_VERSION, got=db_version)
    yield


def create_app() -> fastapi.FastAPI:
    """Create the FastAPI application."""
    app = fastapi.FastAPI(
        title="Chatrooms API",
        description="""API for Chatrooms project.""",
        version=VERSION,
        lifespan=lifespan,
    )

    app.include_router(routers.files.router)
    app.include_router(routers.general.router)
    app.include_router(routers.user.router)
    app.include_router(routers.messages.router)
    app.include_router(routers.rooms.router)
    app.include_router(routers.todos.router)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app
