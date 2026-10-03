# gsc-cli

A Google Search Console CLI that doubles as the backend for a set of Claude Code
SEO-analysis skills. Humans use it directly; skills shell out to the installed
`gsc` binary with `--format json` and reason over the output.

## Quick start

```bash
uv sync                       # create the venv + install deps + register `gsc`
uv run gsc auth login         # OAuth2 browser flow -> saves the `default` profile
uv run gsc sites list         # confirm access
uv run gsc --format json query https://www.example.com/ \
    --start-date 2026-01-01 --end-date 2026-01-28 --dimensions query
```

Set `GSC_CLIENT_SECRETS` to your OAuth2 `client_secrets.json` (downloaded from the
Google Cloud Console) before `gsc auth login`, or pass `--client-secrets`.

## Project structure

```
src/gsc/
  __init__.py        # __version__
  models.py          # API response dataclasses + Profile (from_api classmethods)
  formatters.py      # format_output -> json / table / csv
  auth.py            # OAuth2 + service-account creds, YAML profile store
  client.py          # GSCClient over webmasters v3 + searchconsole v1
  cli/
    main.py          # root `cli` group, global --profile/--format/--verbose
    auth_cmd.py      # `gsc auth` (login, add-profile, list/remove-profile, status)
    sites.py         # `gsc sites` + shared get_client(ctx) factory
    query.py         # `gsc query` + parse_filter
    sitemaps.py      # `gsc sitemaps` (list, get, submit, delete)
    inspect_cmd.py   # `gsc inspect`
    multimodal.py    # `gsc multimodal` (UI export of Web: multimodal; not in the API)
    genai.py         # `gsc genai` (UI export of the Generative AI report + AI lift index)
.claude-plugin/      # marketplace.json, so `/plugin marketplace add` finds the plugin
plugins/gsc-cli/     # the Claude Code plugin: .claude-plugin/plugin.json + skills/
```

## Three-layer architecture

1. **Core library** (`src/gsc/`) — `GSCClient` wraps the two discovery services;
   methods return dataclasses parsed via `from_api`. `auth.py` resolves a
   `Profile` to Google `Credentials`. `formatters.py` renders output.
2. **Click CLI** (`src/gsc/cli/`) — a root group stashes global options in
   `ctx.obj`; each data command sets `ctx.obj["site_url"]`, builds a client via
   `get_client(ctx)`, flattens the returned dataclass to plain dicts, and calls
   `format_output`.
3. **Claude Code skills** (`plugins/gsc-cli/skills/`) — markdown files that invoke
   `gsc --format json <command>` and analyze the JSON. They never touch the
   Google API directly. `gsc-core` is an always-loaded reference; the rest are
   user-triggered.

## Multi-profile auth model

Profiles live in `~/.config/gsc/config.yaml` (override the directory with
`GSC_CONFIG_DIR`):

```yaml
profiles:
  default:
    auth_type: oauth2
    credentials: ~/.config/gsc/oauth/default.json
    sites: []
  client-acme:
    auth_type: service_account
    credentials: /keys/acme-sa.json
    sites: ["https://www.acme.com/", "sc-domain:acme.com"]
```

A command resolves its profile by precedence:

1. explicit `--profile NAME` (or `$GSC_PROFILE`);
2. otherwise, the profile whose `sites` list contains the target site URL
   (auto-detection);
3. otherwise, `default`.

OAuth login always requests read-write scope. For service accounts,
`get_credentials(profile, writable=...)` picks readonly vs read-write — the
`sitemaps submit`/`delete` commands request writable credentials.

## Conventions

- Run everything through `uv run` (e.g. `uv run gsc ...`).
- `--format` is **global** and precedes the subcommand:
  `gsc --format json query ...`, not `gsc query --format json ...`.
- Filters use the form `'dimension operator expression'`, e.g.
  `--filter 'query contains running shoes'`. `--filter` is repeatable and the
  filters are AND-combined.
- Site URLs are either `https://www.example.com/` (with trailing slash) or
  `sc-domain:example.com`.
- Date convention for the analysis skills: **end date = today − 3 days** (GSC data
  lags ~2–3 days).
- Python 3.11+, `from __future__ import annotations` in every module, full type
  hints. Lint/format with `ruff` (line-length 100): `uv run ruff check .`.
