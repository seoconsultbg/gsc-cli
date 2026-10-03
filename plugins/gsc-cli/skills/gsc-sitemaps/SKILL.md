---
name: gsc-sitemaps
description: List, inspect, submit, and delete sitemaps for a Google Search Console property via the gsc CLI. Use when the user wants to check sitemap health or manage submitted sitemaps.
allowed-tools: Bash(gsc *)
---

# gsc-sitemaps

Manage and inspect sitemaps. See `gsc-core` for global flags. Submit/delete need a
profile with write access.

## Usage

List sitemaps:

```bash
gsc --format json sitemaps list "<SITE_URL>"
```

→ rows of `{ path, last_submitted, last_downloaded, is_pending, is_sitemaps_index,
type, warnings, errors, contents:[{type, submitted, indexed}] }`.

Get one:

```bash
gsc --format json sitemaps get "<SITE_URL>" "<FEEDPATH>"
```

Submit / delete (write access required):

```bash
gsc --format json sitemaps submit "<SITE_URL>" "https://www.example.com/sitemap.xml"
gsc --format json sitemaps delete "<SITE_URL>" "https://www.example.com/sitemap.xml"
```

## Workflow

1. `sitemaps list` for the property.
2. For health, compare per-`contents` `submitted` vs `indexed`, and read `warnings`,
   `errors`, `is_pending`, and `last_downloaded`.

## Presentation

Table of sitemaps with an indexed/submitted ratio per content type. Flag entries
with errors > 0, large submitted-vs-indexed gaps, `is_pending = true`, or a stale
`last_downloaded`. Before any `submit`/`delete`, confirm the intent with the user —
these mutate the property.
