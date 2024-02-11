"""Migration CLI."""


import asyncio
import logging

import typer

from chatrooms.database.migrations import core
from chatrooms.settings import get_settings

cli = typer.Typer()


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
def up() -> None:
    """Run one up migration."""
    settings = get_settings()
    done = asyncio.run(core.one_up(settings))
    typer.echo(f"Done: {done}")


@cli.command()
def down() -> None:
    """Run one down migration."""
    settings = get_settings()
    done = asyncio.run(core.one_down(settings))
    typer.echo(f"Done: {done}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  [%(levelname)-10s] %(message)-60s [%(name)-10s]",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    typer.run(cli)
