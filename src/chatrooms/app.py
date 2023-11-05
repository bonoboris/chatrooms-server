"""Main app file."""

import fastapi
from fastapi.middleware.cors import CORSMiddleware

from chatrooms import VERSION, routers


def create_app() -> fastapi.FastAPI:
    """Create the FastAPI application."""
    app = fastapi.FastAPI(
        title="Chatrooms API",
        description="""API for Chatrooms project.""",
        version=VERSION,
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
