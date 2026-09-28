"""``gsc sitemaps`` group: list, get, submit, delete."""

from __future__ import annotations

from dataclasses import asdict

import click

from ..formatters import format_output
from .sites import get_client


@click.group()
def sitemaps() -> None:
    """List and manage submitted sitemaps."""


@sitemaps.command("list")
@click.argument("site_url")
@click.pass_context
def list_sitemaps(ctx: click.Context, site_url: str) -> None:
    """List all sitemaps for SITE_URL."""
    ctx.obj["site_url"] = site_url
    client = get_client(ctx)
    rows = [asdict(s) for s in client.list_sitemaps(site_url)]
    click.echo(format_output(rows, fmt=ctx.obj["format"]))


@sitemaps.command("get")
@click.argument("site_url")
@click.argument("feedpath")
@click.pass_context
def get_sitemap(ctx: click.Context, site_url: str, feedpath: str) -> None:
    """Show details for a single sitemap FEEDPATH."""
    ctx.obj["site_url"] = site_url
    client = get_client(ctx)
    sitemap = client.get_sitemap(site_url, feedpath)
    click.echo(format_output(asdict(sitemap), fmt=ctx.obj["format"]))


@sitemaps.command("submit")
@click.argument("site_url")
@click.argument("feedpath")
@click.pass_context
def submit_sitemap(ctx: click.Context, site_url: str, feedpath: str) -> None:
    """Submit FEEDPATH as a sitemap for SITE_URL."""
    ctx.obj["site_url"] = site_url
    client = get_client(ctx, writable=True)
    client.submit_sitemap(site_url, feedpath)
    click.echo(format_output({"submitted": feedpath, "site_url": site_url}, fmt=ctx.obj["format"]))


@sitemaps.command("delete")
@click.argument("site_url")
@click.argument("feedpath")
@click.pass_context
def delete_sitemap(ctx: click.Context, site_url: str, feedpath: str) -> None:
    """Delete (unsubmit) sitemap FEEDPATH for SITE_URL."""
    ctx.obj["site_url"] = site_url
    client = get_client(ctx, writable=True)
    client.delete_sitemap(site_url, feedpath)
    click.echo(format_output({"deleted": feedpath, "site_url": site_url}, fmt=ctx.obj["format"]))
