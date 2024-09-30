"""Authentication and authorization."""

from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, Self

import fastapi
import pydantic
from fastapi import (
    status,
)
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.security.utils import get_authorization_scheme_param
from jose import JWTError, jwt
from passlib.context import CryptContext

from chatrooms import schemas
from chatrooms.database import queries
from chatrooms.database.connections import DB
from chatrooms.settings import Settings

TOKEN_TYPE = "bearer"  # noqa: S105
TOKEN_URL = "/login"  # noqa: S105
ALGORITHM = "HS256"
CREDENTIALS_EXCEPTION = fastapi.HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


BCRYPT = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Token(pydantic.BaseModel):
    """JWT token."""

    access_token: str
    token_type: str = TOKEN_TYPE


class TokenData(pydantic.BaseModel):
    """JWT token with data."""

    username: str


def hash_password(password: str) -> str:
    """Hash password."""
    return BCRYPT.hash(password)


async def authenticate_user(db: DB, username: str, password: str) -> schemas.UserDB | None:
    """Authenticate user from database."""
    user = await queries.select_user_by_username(db, username)
    if user is None:
        return None
    if not BCRYPT.verify(password, user.digest):
        return None
    return user


def create_access_token(data: dict[str, Any], secret_key: str, expires_delta: timedelta) -> str:
    """Create an JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(tz=UTC) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(claims=to_encode, key=secret_key, algorithm=ALGORITHM)


async def login(
    response: fastapi.Response,
    db: DB,
    settings: Settings,
    form_data: OAuth2PasswordRequestForm,
    *,
    use_cookie: bool = False,
) -> Token:
    """Log user in and return the access JWT token."""
    user = await authenticate_user(db, form_data.username, form_data.password)
    if user is None:
        raise fastapi.HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.username},
        secret_key=settings.secret_key.get_secret_value(),
        expires_delta=timedelta(seconds=settings.access_token_expires),
    )
    if use_cookie:
        response.set_cookie(
            key="Authorization",
            value=f"Bearer {access_token}",
            max_age=settings.cookie_max_age,
            httponly=True,
            secure=True,
            path="/",
            samesite="lax",
        )

    return Token(access_token=access_token)


# --- Dependencies ---

LoginFormData = Annotated[OAuth2PasswordRequestForm, fastapi.Depends()]


class OAuth2PasswordBearerCookie(OAuth2PasswordBearer):
    """OAuth2PasswordBearer with cookie support."""

    async def __call__(self: Self, request: fastapi.Request) -> str | None:
        """Get token from cookie or header."""
        authorization = request.cookies.get("Authorization", request.headers.get("Authorization"))
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != TOKEN_TYPE:
            if self.auto_error:
                raise CREDENTIALS_EXCEPTION
            return None
        return param


BEARER_COOKIE = OAuth2PasswordBearerCookie(tokenUrl=TOKEN_URL)

BearerToken = Annotated[str, fastapi.Depends(BEARER_COOKIE)]


async def validate_token(db: DB, settings: Settings, token: str) -> schemas.UserDB:
    """Validate token, if valid return UserDB instance, otherwise raise HTTP 401 exception."""
    try:
        payload = jwt.decode(
            token=token,
            key=settings.secret_key.get_secret_value(),
            algorithms=[ALGORITHM],
        )
    except JWTError as err:
        raise CREDENTIALS_EXCEPTION from err

    username: str | None = payload.get("sub")
    if username is None:
        raise CREDENTIALS_EXCEPTION
    token_data = TokenData(username=username)
    user = await queries.select_user_by_username(db, token_data.username)
    if user is None:
        raise CREDENTIALS_EXCEPTION
    return user


async def get_current_user(db: DB, settings: Settings, token: BearerToken) -> schemas.UserDB:
    """Authed user dependency."""
    return await validate_token(db, settings, token)


CurrentUser = Annotated[schemas.UserFull, fastapi.Depends(get_current_user)]


async def get_current_active_user(current_user: CurrentUser) -> CurrentUser:
    """Authed active user dependency."""
    if not current_user.is_active:
        raise fastapi.HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user


ActiveUser = Annotated[schemas.UserFull, fastapi.Depends(get_current_active_user)]


# --- WS Dependencies ---


def get_bearer_token_from_websocket(ws: fastapi.WebSocket) -> str:
    """Get bearer token value from WebSocket."""
    authorization = ws.cookies.get("Authorization", ws.headers.get("Authorization"))
    scheme, param = get_authorization_scheme_param(authorization)
    if not authorization or scheme.lower() != TOKEN_TYPE:
        raise fastapi.WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    return param


WebSocketBearerToken = Annotated[str, fastapi.Depends(get_bearer_token_from_websocket)]


async def get_current_user_from_websocket(
    db: DB, settings: Settings, token: WebSocketBearerToken
) -> schemas.UserDB:
    """Auth user dependency for websockets."""
    return await validate_token(db, settings, token)


WebSocketCurrentUser = Annotated[schemas.UserFull, fastapi.Depends(get_current_user_from_websocket)]


async def get_current_active_user_from_websocket(
    current_user: WebSocketCurrentUser,
) -> WebSocketCurrentUser:
    """Authed active user dependency."""
    if not current_user.is_active:
        raise fastapi.HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user


WebSocketActiveUser = Annotated[
    schemas.UserFull, fastapi.Depends(get_current_active_user_from_websocket)
]
