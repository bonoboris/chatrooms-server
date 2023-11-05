"""General related routes."""

from typing import Literal

import fastapi
import pydantic
from fastapi import responses, status

from chatrooms import auth
from chatrooms.database.connections import DB
from chatrooms.routers.commons import default_errors
from chatrooms.settings import Settings

router = fastapi.APIRouter(tags=["general"])


@router.get("/")
async def index() -> responses.RedirectResponse:
    """Hello world route."""
    return responses.RedirectResponse("/docs", status_code=status.HTTP_308_PERMANENT_REDIRECT)


class Status(pydantic.BaseModel):
    """GET /status response schema."""

    status: Literal["ok"]


@router.get("/status")
async def get_status() -> Status:
    """Get server status route."""
    return Status(status="ok")


@router.post("/login", responses=default_errors(status.HTTP_401_UNAUTHORIZED))
async def login(
    response: fastapi.Response,
    db: DB,
    settings: Settings,
    form_data: auth.LoginFormData,
    use_cookie: bool = False,  # noqa: FBT001, FBT002
) -> auth.Token:
    """Login route."""
    return await auth.login(
        response=response,
        db=db,
        settings=settings,
        form_data=form_data,
        use_cookie=use_cookie,
    )


@router.post("/logout")
async def logout(response: fastapi.Response) -> None:
    """Logout route."""
    response.delete_cookie("Authorization", secure=True, httponly=True)
