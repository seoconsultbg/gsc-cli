"""``gsc inspect`` command: single-URL index inspection."""

from __future__ import annotations

from dataclasses import asdict

import click

from ..formatters import format_output
from .sites import get_client


@click.command()
@click.argument("site_url")
@click.argument("inspection_url")
@click.pass_context
def inspect_url(ctx: click.Context, site_url: str, inspection_url: str) -> None:
    """Inspect INSPECTION_URL in SITE_URL's index."""
    ctx.obj["site_url"] = site_url
    client = get_client(ctx)
    result = client.inspect_url(site_url, inspection_url)

    out: dict = {"inspection_result_link": result.inspection_result_link}
    if result.index_status is not None:
        out.update(asdict(result.index_status))
    click.echo(format_output(out, fmt=ctx.obj["format"]))
