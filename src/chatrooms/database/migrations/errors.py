"""Migration subpackage errors."""

from typing import Self


class MigrationError(Exception):
    """Migration error."""


class MissingMigrationVersionError(MigrationError):
    """Missing migration version error."""

    def __init__(self: Self) -> None:
        super().__init__("Missing `VERSION` class attribute from miggration class.")


class DatabaseVersionError(RuntimeError):
    """Expected DB version & actual version mismatch."""

    def __init__(self: Self, expected: int, got: int) -> None:
        super().__init__(f"Database version & API version mismatch: expected={expected}, got={got}")
        self.expected = expected
        self.got = got
