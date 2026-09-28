---
name: gsc-sites
description: List and inspect verified Google Search Console properties via the gsc CLI. Use when the user wants to see which sites/properties are available or check access to a specific property.
allowed-tools: Bash(gsc *)
---

# gsc-sites

List the Search Console properties the active profile can access, or get details
for one. See `gsc-core` for global flags and the profile model.

## Usage

List every accessible property:

```bash
gsc --format json sites list
```

→ `[{ "site_url": "...", "permission_level": "..." }, ...]`

Get one property:

```bash
gsc --format json sites get "https://www.example.com/"
```

→ `{ "site_url": "...", "permission_level": "siteOwner|siteFullUser|..." }`

## Notes

- Site URLs are `https://www.example.com/` (trailing slash) or `sc-domain:example.com`.
- If a specific site is wanted, pass `--profile` or rely on auto-detection — a
  profile whose `sites` list contains the URL is selected automatically.

## Presentation

Render a short table of `site_url` + `permission_level`. If `sites list` is empty,
the profile has no verified properties — suggest `gsc auth login` or checking the
profile.
