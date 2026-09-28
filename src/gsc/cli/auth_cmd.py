"""``gsc auth`` command group and a ``--config-path`` decorator for test isolation."""

from __future__ import annotations

import os
from pathlib import Path

import click

from ..auth import (
    CONFIG_PATH,
    add_service_account_profile,
    get_credentials,
    list_profiles,
    remove_profile,
    resolve_profile,
    run_oauth_flow,
)
from ..formatters import format_output


def _config_path_option(func):
    """Attach a ``--config-path`` option that flows into ``ctx.obj``."""

    def callback(ctx: click.Context, param, value):
        ctx.ensure_object(dict)
        if value:
            ctx.obj["config_path"] = value
        return value

    return click.option(
        "--config-path",
        default=None,
        expose_value=False,
        is_eager=True,
        callback=callback,
        help="Override the config.yaml path (for testing / isolation).",
    )(func)


def _get_config_path(ctx: click.Context) -> Path:
    """Resolve the active config path from ctx.obj, else the default."""
    path = ctx.obj.get("config_path") if ctx.obj else None
    return Path(path) if path else CONFIG_PATH


@click.group()
def auth() -> None:
    """Manage authentication and profiles."""


@auth.command("login")
@_config_path_option
@click.option(
    "--client-secrets",
    default=lambda: os.environ.get("GSC_CLIENT_SECRETS"),
    help="Path to OAuth2 client_secrets.json (default: $GSC_CLIENT_SECRETS).",
)
@click.pass_context
def login(ctx: click.Context, client_secrets: str | None) -> None:
    """Run the OAuth2 browser flow and save the 'default' profile."""
    if not client_secrets:
        raise click.ClickException("Provide --client-secrets or set $GSC_CLIENT_SECRETS.")
    profile = run_oauth_flow(client_secrets, config_path=_get_config_path(ctx))
    click.echo(f"Logged in. Saved profile '{profile.name}' ({profile.credentials}).")


@auth.command("add-profile")
@_config_path_option
@click.argument("name")
@click.option(
    "--service-account",
    "credentials",
    required=True,
    help="Path to the service-account JSON key file.",
)
@click.option(
    "--site",
    "sites",
    multiple=True,
    help="Site URL this profile manages (repeatable; enables auto-detection).",
)
@click.pass_context
def add_profile(ctx: click.Context, name: str, credentials: str, sites: tuple[str, ...]) -> None:
    """Add a service-account profile NAME."""
    profile = add_service_account_profile(
        name=name,
        credentials=credentials,
        sites=list(sites),
        config_path=_get_config_path(ctx),
    )
    click.echo(f"Added service-account profile '{profile.name}'.")


@auth.command("list-profiles")
@_config_path_option
@click.pass_context
def list_profiles_cmd(ctx: click.Context) -> None:
    """List all configured profiles."""
    profiles = list_profiles(config_path=_get_config_path(ctx))
    rows = [
        {
            "name": p.name,
            "auth_type": p.auth_type,
            "credentials": p.credentials,
            "sites": ", ".join(p.sites),
        }
        for p in profiles
    ]
    click.echo(format_output(rows, fmt=ctx.obj["format"]))


@auth.command("remove-profile")
@_config_path_option
@click.argument("name")
@click.pass_context
def remove_profile_cmd(ctx: click.Context, name: str) -> None:
    """Remove profile NAME."""
    removed = remove_profile(name, config_path=_get_config_path(ctx))
    if not removed:
        raise click.ClickException(f"No such profile: {name}")
    click.echo(f"Removed profile '{name}'.")


@auth.command("status")
@_config_path_option
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show the active profile and whether its credentials load."""
    profile = resolve_profile(name=ctx.obj.get("profile"), config_path=_get_config_path(ctx))
    if profile is None:
        raise click.ClickException("No active profile. Run 'gsc auth login'.")

    info: dict = {
        "name": profile.name,
        "auth_type": profile.auth_type,
        "credentials": profile.credentials,
        "sites": ", ".join(profile.sites),
    }
    try:
        get_credentials(profile)
        info["credentials_ok"] = True
    except Exception as exc:  # noqa: BLE001
        info["credentials_ok"] = False
        if ctx.obj.get("verbose"):
            info["error"] = str(exc)
    click.echo(format_output(info, fmt=ctx.obj["format"]))
