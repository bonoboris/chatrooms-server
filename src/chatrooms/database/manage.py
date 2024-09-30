"""CLI to manage the database."""

import asyncio
import datetime
from collections import abc

import typer

from chatrooms import auth, schemas
from chatrooms.database import connections, queries
from chatrooms.settings import Settings, get_settings

cli = typer.Typer(name="manage", help="Manage the database")

users_cli = typer.Typer(name="users", help="Manage users")

cli.add_typer(users_cli, name="users")


async def _create_user(settings: Settings, name: str, email: str, password: str) -> schemas.UserDB:
    """Create a new user in the database."""
    digest = auth.hash_password(password)
    created_at = datetime.datetime.now().astimezone(datetime.UTC)
    async with await connections.get_db_connection(settings) as db:
        return await queries.insert_user(
            db,
            username=name,
            email=email,
            digest=digest,
            is_active=True,
            created_at=created_at,
        )


async def _list_users(settings: Settings) -> list[schemas.UserDB]:
    """List users in the database."""
    async with await connections.get_db_connection(settings) as db:
        return await queries.select_all_users(db)


async def _delete_user(settings: Settings, id: int) -> bool:
    """Delete user by id."""
    async with await connections.get_db_connection(settings) as db:
        return await queries.delete_user_by_id(db, id=id)


def _format_row(row: abc.Sequence[str], widths: abc.Sequence[int]) -> str:
    cells: list[str] = []
    for cell, width in zip(row, widths, strict=False):
        cells.append(cell.rjust(width))
    return " | ".join(cells) + "\n"


COLS = ("username", "email", "is active ?", "created at")


def format_users(*users: schemas.UserDB) -> str:
    """Format users as a table."""
    data = list[tuple[str, str, str, str]]()
    for user in users:
        data.append(
            (
                user.username,
                user.email,
                str(user.is_active),
                user.created_at.astimezone().isoformat(sep=" ")[:19],
            )
        )
    max_lens = [len(header) for header in COLS]
    for row in data:
        for i, cell in enumerate(row):
            max_lens[i] = max(max_lens[i], len(cell))

    lines: list[str] = [_format_row(COLS, max_lens)]
    lines.append("-|-".join("-" * w for w in max_lens) + "\n")
    lines.extend(_format_row(row, max_lens) for row in data)
    return "".join(lines)


@users_cli.command()
def create(name: str, email: str, password: str) -> None:
    """Create a new user in the database."""
    settings = get_settings()
    user = asyncio.run(_create_user(settings, name, email, password))
    typer.echo("created")
    typer.echo(format_users(user))


@users_cli.command(name="list")
def list_() -> None:
    """List users in the database."""
    settings = get_settings()
    users = asyncio.run(_list_users(settings))

    typer.echo(format_users(*users))


@users_cli.command()
def delete(id: int) -> None:
    """Delete user by id."""
    settings = get_settings()
    deleted = asyncio.run(_delete_user(settings, id))
    if deleted:
        typer.echo(f"{id} deleted")
    else:
        typer.echo(f"{id} not found")
