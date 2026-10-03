---
name: gsc-query
description: Query Google Search Console Search Analytics (clicks, impressions, CTR, position) via the gsc CLI, broken down by query, page, country, device, or date with optional filters. Use for ad-hoc performance lookups.
allowed-tools: Bash(gsc *)
---

# gsc-query

Run raw Search Analytics queries. For multi-step analyses prefer `gsc-analyze`,
`gsc-compare`, `gsc-cannibalization`, or `gsc-opportunities`. See `gsc-core` for the
date convention (end = today − 3) and benchmarks.

## Usage

```bash
gsc --format json query "<SITE_URL>" \
    --start-date 2026-01-01 --end-date 2026-01-28 \
    --dimensions query \
    --row-limit 100
```

Common variants:

- Top pages: `--dimensions page`
- Device split: `--dimensions device`
- Daily trend: `--dimensions date`
- Filtered: `--filter 'query contains running'` (repeatable, AND-combined)
- Page + query pairs: `--dimensions page,query`

Each row: `{<dimensions...>, clicks, impressions, ctr, position}` where `ctr` is a
string like `"3.45%"` and `position` is rounded to 1 decimal.

## Workflow

1. Resolve the window from the user's request using end = today − 3.
2. Run the `gsc --format json query` call with the requested dimensions/filters.
3. Parse the JSON rows.

## Presentation

Show a table sorted by the metric the user cares about (clicks by default).
Summarize totals (sum clicks/impressions, impression-weighted avg position). Flag
anything noteworthy against `gsc-core` benchmarks (e.g. striking-distance rows).
