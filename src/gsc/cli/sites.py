"""``gsc sites`` group and the shared client factory."""

from __future__ import annotations

from dataclasses import asdict

import click

from ..auth import get_credentials, resolve_profile
from ..client import GSCClient
from ..formatters import format_output


def get_client(ctx: click.Context, writable: bool = False) -> GSCClient:
    """Resolve a profile from ``ctx.obj`` and build a :class:`GSCClient`.

    Honours an explicit ``--profile`` first, then auto-detects from
    ``ctx.obj["site_url"]`` (set by data commands), then falls back to
    ``default``.
    """
    profile_name = ctx.obj.get("profile")
    site_url = ctx.obj.get("site_url")
    profile = resolve_profile(name=profile_name, site_url=site_url)
    if profile is None:
        raise click.ClickException(
            "No matching auth profile. Run 'gsc auth login' or 'gsc auth add-profile' first."
        )
    credentials = get_credentials(profile, writable=writable)
    return GSCClient(credentials)


@click.group()
def sites() -> None:
    """List and inspect verified Search Console properties."""


@sites.command("list")
@click.pass_context
def list_sites(ctx: click.Context) -> None:
    """List all properties you can access."""
    client = get_client(ctx)
    rows = [asdict(site) for site in client.list_sites()]
    click.echo(format_output(rows, fmt=ctx.obj["format"]))


@sites.command("get")
@click.argument("site_url")
@click.pass_context
def get_site(ctx: click.Context, site_url: str) -> None:
    """Show details for a single property."""
    ctx.obj["site_url"] = site_url
    client = get_client(ctx)
    site = client.get_site(site_url)
    click.echo(format_output(asdict(site), fmt=ctx.obj["format"]))
