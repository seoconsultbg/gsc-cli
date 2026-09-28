"""Root Click group with global options, registering all subcommands."""

from __future__ import annotations

import os

import click

from .. import __version__


@click.group()
@click.option(
    "--profile",
    "-p",
    default=lambda: os.environ.get("GSC_PROFILE"),
    help="Auth profile name (default: $GSC_PROFILE, else auto-detect).",
)
@click.option(
    "--format",
    "-f",
    "fmt",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
    help="Output format. Global; precedes the subcommand.",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose error output.")
@click.version_option(__version__, prog_name="gsc")
@click.pass_context
def cli(ctx: click.Context, profile: str | None, fmt: str, verbose: bool) -> None:
    """gsc — Google Search Console from the command line."""
    ctx.ensure_object(dict)
    ctx.obj["profile"] = profile
    ctx.obj["format"] = fmt
    ctx.obj["verbose"] = verbose


from .auth_cmd import auth  # noqa: E402
from .genai import genai  # noqa: E402
from .inspect_cmd import inspect_url  # noqa: E402
from .multimodal import multimodal  # noqa: E402
from .query import query  # noqa: E402
from .sitemaps import sitemaps  # noqa: E402
from .sites import sites  # noqa: E402

cli.add_command(auth)
cli.add_command(sites)
cli.add_command(query)
cli.add_command(sitemaps)
cli.add_command(inspect_url, name="inspect")
cli.add_command(multimodal)
cli.add_command(genai)
