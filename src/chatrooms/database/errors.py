"""Database errors."""

from typing import Self


class DatabaseError(Exception):
    """Database error."""


class NotFoundAfterInsertError(DatabaseError):
    """Not found after insert error."""

    def __init__(self: Self, table: str) -> None:
        super().__init__(f"Failed to find record in table {table} after insert")
