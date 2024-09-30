"""Migration CLI."""

import asyncio
import logging

import typer

from chatrooms.database.migrations import core
from chatrooms.settings import get_settings

cli = typer.Typer(name="migrate", help="Manage database migrations")


@cli.callback()
def _cli(verbose: bool = False) -> None:  # pyright: ignore[reportUnusedFunction]  # noqa: FBT001, FBT002
    """Manage database migrations."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s  [%(levelname)-10s] %(message)-60s [%(name)-10s]",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@cli.command()
def version() -> None:
    """Print database current version."""
    settings = get_settings()
    version = asyncio.run(core.get_version(settings))
    typer.echo(f"version: {version}")


@cli.command()
def up(all: bool = True) -> None:  # noqa: A002, FBT001, FBT002
    """Run one or all up migration(s)."""
    settings = get_settings()
    _run = core.all_up if all else core.one_up
    asyncio.run(_run(settings))


@cli.command()
def down(all: bool = True) -> None:  # noqa: A002, FBT001, FBT002
    """Run one or all down migration(s)."""
    settings = get_settings()
    _run = core.all_down if all else core.one_down
    asyncio.run(_run(settings))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  [%(levelname)-10s] %(message)-60s [%(name)-10s]",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    typer.run(cli)
