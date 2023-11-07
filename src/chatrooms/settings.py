"""Chatrooms API settings."""

import functools
from typing import Annotated

import pydantic_settings
from fastapi import Depends


class SettingsModel(pydantic_settings.BaseSettings):
    """Chatrooms API settings."""

    secret_key: str = "secret"
    """Secret key used to sign JWT tokens."""
    access_token_expires: int = 10 * 60
    """Access token expiration time in seconds."""
    refresh_token_expires: int = 30 * 24 * 60 * 60
    """Refresh token expiration time in seconds."""
    cookie_max_age: int = 2 * 60 * 60
    """Cookie max age in seconds."""

    pg_username: str = "postgres"
    """PostgreSQL database user name."""
    pg_password: str = "postgres"
    """PostgreSQL database user password."""
    pg_host: str = "localhost"
    """PostgreSQL database host."""
    pg_port: int = 5432
    """PostgreSQL database port."""
    pg_database: str = "chatrooms"
    """PostgreSQL database name."""

    fs_root: str = "/data/chatrooms"
    """File systeme root folder for uploaded files."""

    model_config = pydantic_settings.SettingsConfigDict(
        env_prefix="chatrooms_api_", env_file=".env"
    )


@functools.lru_cache
def get_settings() -> SettingsModel:
    """Get settings, (chached)."""
    return SettingsModel()


Settings = Annotated[SettingsModel, Depends(get_settings)]
