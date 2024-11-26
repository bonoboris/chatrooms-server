"""CLI to manage the database."""

import asyncio
import datetime
import pathlib
import subprocess
from collections import abc

import pydantic
import typer

from chatrooms import auth, schemas
from chatrooms.database import connections, queries
from chatrooms.settings import get_settings

DUMPDIR = pathlib.Path("dbdump")

cli = typer.Typer(name="manage", help="Manage the database", no_args_is_help=True)

users_cli = typer.Typer(name="users")
rooms_cli = typer.Typer(name="rooms")


cli.add_typer(users_cli, name="users")
cli.add_typer(rooms_cli, name="rooms")

####################################################################################################
# Top level commands
####################################################################################################


@cli.command()
def dump() -> None:
    """Dump the database in directory format."""
    settings = get_settings()
    cmd = ["pg_dump"]
    if settings.pg_user:
        cmd.append(f"--username={settings.pg_user}")
    if settings.pg_host:
        cmd.append(f"--host={settings.pg_host}")
    if settings.pg_port:
        cmd.append(f"--port={settings.pg_port}")
    cmd.append(f"--dbname={settings.pg_database}")
    cmd.append("--format=d")
    timestamp = datetime.datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    DUMPDIR.mkdir(parents=True, exist_ok=True)
    file = DUMPDIR / f"{settings.pg_database}_{timestamp}"
    file.mkdir()
    cmd.append(f"--file={file}")
    typer.echo(" ".join(cmd))
    try:
        subprocess.run(cmd, check=True)  # noqa: S603
    except subprocess.CalledProcessError:
        raise typer.Exit(code=1) from None

    typer.echo(file)


@cli.command()
def restore(file: pathlib.Path, data_only: bool = False) -> None:  # noqa: FBT001, FBT002
    """Restore the database from directory format."""
    settings = get_settings()
    cmd = ["pg_restore"]
    if settings.pg_user:
        cmd.append(f"--username={settings.pg_user}")
    if settings.pg_host:
        cmd.append(f"--host={settings.pg_host}")
    if settings.pg_port:
        cmd.append(f"--port={settings.pg_port}")
    cmd.append(f"--dbname={settings.pg_database}")

    cmd.append("--format=d")

    if data_only:
        cmd.append("--data-only")
    else:
        cmd.append("--clean --if-exists")
    cmd.append(str(file))

    try:
        subprocess.run(cmd, check=True)  # noqa: S603
    except subprocess.CalledProcessError:
        raise typer.Exit(code=1) from None

    typer.echo("Done!")


####################################################################################################
# users commands
####################################################################################################


@users_cli.callback(invoke_without_command=True)
def users_callback(ctx: typer.Context) -> None:
    """Manage users."""
    if ctx.invoked_subcommand is None:
        list_users()


@users_cli.command(name="list")
def list_users() -> None:
    """List users in the database (default)."""
    settings = get_settings()

    async def _run() -> list[schemas.UserDB]:
        async with await connections.get_db_connection(settings) as db:
            return await queries.select_all_users(db)

    users = asyncio.run(_run())
    typer.echo(format_table(users, ["id", "username", "email", "is_active", "created_at"]))


@users_cli.command(name="create")
def create_user(name: str, email: str, password: str) -> None:
    """Create a new user in the database."""
    settings = get_settings()

    async def _run() -> schemas.UserDB:
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

    user = asyncio.run(_run())
    typer.echo("created")
    typer.echo(format_table([user], ["id", "username", "email", "is_active", "created_at"]))


@users_cli.command(name="reset-password")
def reset_password(id: int, password: str) -> None:
    """Reset user's password."""
    settings = get_settings()

    async def _run() -> schemas.UserDB:
        async with await connections.get_db_connection(settings) as db:
            digest = auth.hash_password(password)
            user = await queries.update_user_digest_by_id(db, id=id, digest=digest)
            if user is None:
                typer.echo(f"User {id} not found")
                raise typer.Exit(code=1)
            return user

    user = asyncio.run(_run())
    typer.echo("password reset")
    typer.echo(format_table([user], ["id", "username", "email", "is_active", "created_at"]))


@users_cli.command(name="delete")
def delete_user(id: int) -> None:
    """Delete user by id."""
    settings = get_settings()

    async def _run() -> bool:
        async with await connections.get_db_connection(settings) as db:
            return await queries.delete_user_by_id(db, id=id)

    deleted = asyncio.run(_run())
    if deleted:
        typer.echo(f"{id} deleted")
    else:
        typer.echo(f"{id} not found")


####################################################################################################
# rooms commands
####################################################################################################


@rooms_cli.callback(invoke_without_command=True)
def rooms_callback(ctx: typer.Context) -> None:
    """Manage rooms."""
    if ctx.invoked_subcommand is None:
        list_rooms()


@rooms_cli.command(name="list")
def list_rooms(limit: int = 100, offset: int = 0) -> None:
    """List rooms in the database (default)."""
    settings = get_settings()

    async def _run() -> list[schemas.Room]:
        async with await connections.get_db_connection(settings) as db:
            return await queries.select_all_rooms(db, limit=limit, offset=offset)

    rooms = asyncio.run(_run())
    typer.echo(format_table(rooms, ["id", "name", "created_by", "created_at"]))


@rooms_cli.command(name="create")
def create_room(name: str, username: str) -> None:
    """Create a new room in the database."""
    settings = get_settings()

    async def _run() -> schemas.Room:
        async with await connections.get_db_connection(settings) as db:
            user = await queries.select_user_by_username(db, username=username)
            if user is None:
                typer.echo(f"User {username} not found")
                raise typer.Exit(code=1)
            return await queries.insert_room(
                db, name=name, created_by=1, created_at=datetime.datetime.now(datetime.UTC)
            )

    created = asyncio.run(_run())
    typer.echo("created")
    typer.echo(format_table([created], ["id", "name", "created_by", "created_at"]))


@rooms_cli.command(name="delete")
def delete_room(id: int) -> None:
    """Delete room by id."""
    settings = get_settings()

    async def _run() -> bool:
        async with await connections.get_db_connection(settings) as db:
            return await queries.delete_room_by_id(db, id=id)

    deleted = asyncio.run(_run())
    if deleted:
        typer.echo(f"{id} deleted")
    else:
        typer.echo(f"{id} not found")


####################################################################################################
# Table formatter
####################################################################################################


def _format_val(val: object) -> str:
    if isinstance(val, datetime.datetime):
        return val.astimezone().strftime("%Y-%m-%d %H:%M:%S")
    return str(val)


def _format_row(row: abc.Sequence[str], widths: abc.Sequence[int]) -> str:
    cells: list[str] = []
    for cell, width in zip(row, widths, strict=False):
        cells.append(cell.rjust(width))
    return " │ ".join(cells) + "\n"


def format_table(models: abc.Sequence[pydantic.BaseModel], fields: abc.Sequence[str]) -> str:
    """Format a sequence of pydantic models as a table.

    Args:
        models: The models to format.
        fields: The fields to include in the table.
    """
    data = list[tuple[str, ...]]()
    for model in models:
        md = model.model_dump(include=set(fields), mode="python")
        data.append(tuple(_format_val(md.get(col)) for col in fields))
    max_lens = [len(header) for header in fields]
    for row in data:
        for i, cell in enumerate(row):
            max_lens[i] = max(max_lens[i], len(cell))

    lines: list[str] = [_format_row(fields, max_lens)]
    lines.append("─┼─".join("─" * w for w in max_lens) + "\n")
    lines.extend(_format_row(row, max_lens) for row in data)
    return "".join(lines)
