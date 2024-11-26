"""Main app file."""

import contextlib
import logging
from collections.abc import AsyncIterator

import fastapi
from fastapi.middleware.cors import CORSMiddleware

from chatrooms import __version__, logs, routers
from chatrooms.database import migrations

LOGGER = logging.getLogger("server")
VERSION = __version__.__version__
DB_VERSION = __version__.DB_VERSION


@contextlib.asynccontextmanager
async def lifespan(_app: fastapi.FastAPI) -> AsyncIterator[None]:
    """Run startup and shutdown events."""
    LOGGER.info("Server startup")
    db_version = await migrations.migration_protocol.MigrationProtocol.get_version()
    if db_version != DB_VERSION:
        raise migrations.errors.DatabaseVersionError(expected=DB_VERSION, got=db_version)
    yield
    LOGGER.info("Server teardown")
    logs.stop_listener()


def create_app() -> fastapi.FastAPI:
    """Create the FastAPI application."""
    logs.configure()
    LOGGER.info("Creating server", extra={"version": VERSION, "db_version": DB_VERSION})
    app = fastapi.FastAPI(
        title="Chatrooms",
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
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:4000",
            "http://127.0.0.1:4000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    LOGGER.info("Server created", extra={"version": VERSION, "db_version": DB_VERSION})
    return app
