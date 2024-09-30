"""Chatrooms API settings."""

import functools
from pathlib import Path
from typing import Annotated

import pydantic_settings
from fastapi import Depends
from pydantic import DirectoryPath, SecretStr


class SettingsModel(pydantic_settings.BaseSettings):
    """Chatrooms API settings."""

    model_config = pydantic_settings.SettingsConfigDict(
        env_prefix="chatrooms_api_", env_file=".env", extra="ignore"
    )

    secret_key: SecretStr = SecretStr("secret")
    """Secret key used to sign JWT tokens."""
    access_token_expires: int = 30 * 60  # 30 minutes
    """Access token expiration time in seconds."""
    refresh_token_expires: int = 30 * 24 * 60 * 60  # 30 days
    """Refresh token expiration time in seconds."""
    cookie_max_age: int = 2 * 60 * 60  # 2 hours
    """Cookie max age in seconds."""

    pg_user: str = "postgres"
    """PostgreSQL database user."""
    pg_password: SecretStr = SecretStr("postgres")
    """PostgreSQL database user password."""
    pg_host: str = ""
    """PostgreSQL database host (empty for unix socket)."""
    pg_port: int = 5432
    """PostgreSQL database port."""
    pg_database: str = "chatrooms"
    """PostgreSQL database name."""

    fs_root: DirectoryPath = Path("/data/chatrooms")
    """File systeme root folder for uploaded files."""


@functools.lru_cache
def get_settings() -> SettingsModel:
    """Get settings, (chached)."""
    return SettingsModel()


Settings = Annotated[SettingsModel, Depends(get_settings)]
