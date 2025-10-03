from __future__ import annotations

import click
from structlog.stdlib import get_logger

from rusttt.logic import print_board, run_perft_inline, set_starting_position

logger = get_logger(__name__)


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Show help when no subcommand is provided."""
    assert ctx is not None, "Click context must be provided"
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
def run() -> None:
    set_starting_position()
    print_board()

    run_perft_inline(6)
    # RunPerftInlineStruct(6)  # noqa: ERA001
