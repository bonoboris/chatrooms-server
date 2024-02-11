"""Chatrooms API settings."""

import functools
from pathlib import Path
from typing import Annotated

import pydantic_settings
from fastapi import Depends
from pydantic import DirectoryPath


class SettingsModel(pydantic_settings.BaseSettings):
    """Chatrooms API settings."""

    secret_key: str = "secret"
    """Secret key used to sign JWT tokens."""
    access_token_expires: int = 30 * 60  # 30 minutes
    """Access token expiration time in seconds."""
    refresh_token_expires: int = 30 * 24 * 60 * 60  # 30 days
    """Refresh token expiration time in seconds."""
    cookie_max_age: int = 2 * 60 * 60  # 2 hours
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

    fs_root: DirectoryPath = Path("/data/chatrooms")
    """File systeme root folder for uploaded files."""

    model_config = pydantic_settings.SettingsConfigDict(
        env_prefix="chatrooms_api_", env_file=".env"
    )


@functools.lru_cache
def get_settings() -> SettingsModel:
    """Get settings, (chached)."""
    return SettingsModel()


Settings = Annotated[SettingsModel, Depends(get_settings)]
