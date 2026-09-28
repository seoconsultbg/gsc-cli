"""OAuth2 + service-account auth and a YAML-backed profile store.

Profiles live in ``config.yaml`` under a top-level ``profiles:`` mapping. Each
profile records its ``auth_type``, a ``credentials`` path, and an optional list
of ``sites`` used for profile auto-detection from a target site URL.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from .models import Profile

SCOPES_READONLY = ["https://www.googleapis.com/auth/webmasters.readonly"]
SCOPES_READWRITE = ["https://www.googleapis.com/auth/webmasters"]


def _config_dir() -> Path:
    override = os.environ.get("GSC_CONFIG_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".config" / "gsc"


CONFIG_DIR = _config_dir()
CONFIG_PATH = CONFIG_DIR / "config.yaml"


def load_config(config_path: Path | str | None = None) -> dict:
    """Load the profile store, returning ``{"profiles": {}}`` if absent."""
    path = Path(config_path) if config_path else CONFIG_PATH
    if not path.exists():
        return {"profiles": {}}
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    data.setdefault("profiles", {})
    return data


def save_config(config: dict, config_path: Path | str | None = None) -> None:
    """Persist the profile store, creating the config dir if needed."""
    path = Path(config_path) if config_path else CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(config, fh, default_flow_style=False, sort_keys=True)


def list_profiles(config_path: Path | str | None = None) -> list[Profile]:
    """Return every stored profile."""
    config = load_config(config_path)
    profiles = []
    for name, data in config.get("profiles", {}).items():
        entry = dict(data or {})
        entry["name"] = name
        profiles.append(Profile.from_api(entry))
    return profiles


def get_profile(name: str, config_path: Path | str | None = None) -> Profile | None:
    """Return a profile by name, or ``None`` if it does not exist."""
    config = load_config(config_path)
    data = config.get("profiles", {}).get(name)
    if data is None:
        return None
    entry = dict(data)
    entry["name"] = name
    return Profile.from_api(entry)


def resolve_profile(
    name: str | None = None,
    site_url: str | None = None,
    config_path: Path | str | None = None,
) -> Profile | None:
    """Resolve a profile by precedence: explicit name, site-URL match, default.

    1. If ``name`` is given, return that profile (or ``None`` if missing).
    2. Else if ``site_url`` matches a profile's ``sites`` list, return it.
    3. Else fall back to the ``default`` profile.
    """
    if name:
        return get_profile(name, config_path)

    if site_url:
        for profile in list_profiles(config_path):
            if site_url in profile.sites:
                return profile

    return get_profile("default", config_path)


def add_service_account_profile(
    name: str,
    credentials: str,
    sites: list[str] | None = None,
    config_path: Path | str | None = None,
) -> Profile:
    """Create / overwrite a service-account profile and persist it."""
    config = load_config(config_path)
    config.setdefault("profiles", {})[name] = {
        "auth_type": "service_account",
        "credentials": str(credentials),
        "sites": list(sites or []),
    }
    save_config(config, config_path)
    return Profile(
        name=name,
        auth_type="service_account",
        credentials=str(credentials),
        sites=list(sites or []),
    )


def remove_profile(name: str, config_path: Path | str | None = None) -> bool:
    """Remove a profile by name; return ``True`` if one was removed."""
    config = load_config(config_path)
    profiles = config.get("profiles", {})
    if name not in profiles:
        return False
    del profiles[name]
    save_config(config, config_path)
    return True


def get_credentials(profile: Profile, writable: bool = False):
    """Build Google credentials for ``profile``.

    OAuth profiles load the saved authorized-user token. Service accounts pick
    the scope based on ``writable``.
    """
    if profile.is_service_account:
        scopes = SCOPES_READWRITE if writable else SCOPES_READONLY
        return service_account.Credentials.from_service_account_file(
            profile.credentials, scopes=scopes
        )

    token_path = (
        Path(profile.credentials)
        if profile.credentials
        else (CONFIG_DIR / "oauth" / "default.json")
    )
    return Credentials.from_authorized_user_file(str(token_path), SCOPES_READWRITE)


def run_oauth_flow(
    client_secrets: str,
    config_path: Path | str | None = None,
) -> Profile:
    """Run the InstalledAppFlow, save the token, and write the ``default`` profile."""
    flow = InstalledAppFlow.from_client_secrets_file(client_secrets, SCOPES_READWRITE)
    creds = flow.run_local_server(port=0)

    token_dir = CONFIG_DIR / "oauth"
    token_dir.mkdir(parents=True, exist_ok=True)
    token_path = token_dir / "default.json"
    with token_path.open("w", encoding="utf-8") as fh:
        fh.write(creds.to_json())

    config = load_config(config_path)
    config.setdefault("profiles", {})["default"] = {
        "auth_type": "oauth2",
        "credentials": str(token_path),
        "sites": [],
    }
    save_config(config, config_path)

    return Profile(
        name="default",
        auth_type="oauth2",
        credentials=str(token_path),
        sites=[],
    )
