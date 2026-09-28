---
name: gsc-analyze
description: 28-day Google Search Console performance overview via the gsc CLI — summary totals, daily trend, top queries and pages, device split, and quick wins. Use when the user wants a health check or "how is my site doing in search".
allowed-tools: Bash(gsc *)
---

# gsc-analyze

A one-shot 28-day performance overview for a property. See `gsc-core` for the date
convention (end = today − 3) and SEO benchmarks.

## Setup

Compute dates from the current date: `END = today − 3`, `START = today − 31`
(28-day window). Resolve `<SITE_URL>` from the user (or `gsc --format json sites
list` if unspecified).

## Workflow

1. Summary totals (no dimensions):

   ```bash
   gsc --format json query "<SITE_URL>" --start-date <START> --end-date <END>
   ```

2. Daily trend:

   ```bash
   gsc --format json query "<SITE_URL>" --start-date <START> --end-date <END> \
       --dimensions date
   ```

3. Top queries:

   ```bash
   gsc --format json query "<SITE_URL>" --start-date <START> --end-date <END> \
       --dimensions query --row-limit 25
   ```

4. Top pages:

   ```bash
   gsc --format json query "<SITE_URL>" --start-date <START> --end-date <END> \
       --dimensions page --row-limit 25
   ```

5. Device split:

   ```bash
   gsc --format json query "<SITE_URL>" --start-date <START> --end-date <END> \
       --dimensions device
   ```

6. Multimodal (image-as-query) share - only if the user has a UI export for the same
   window (Search type -> Web -> Multimodal -> Export; the API cannot filter it, see
   `gsc-core`). Ask for it on image-heavy sites (e-commerce, travel, local, products):

   ```bash
   gsc --format json multimodal "<SITE_URL>" <EXPORT.zip> --compare \
       --start-date <START> --end-date <END>
   ```

   Without an export, say so in the report instead of skipping silently.

## Analysis

- **Summary:** total clicks, impressions, site-wide CTR, impression-weighted avg
  position.
- **Trend:** compare the first vs. last 7 days of the daily series — rising, flat, or
  falling. Note any spikes/drops.
- **Top queries/pages:** which drive the most clicks; flag high-impression /
  low-position (11–20 striking distance) and page-1 / low-CTR rows per `gsc-core`.
- **Device:** clicks/CTR/position by device; call out underperformance (often
  mobile).
- **Multimodal (if exported):** property-level camera share of Web impressions; top
  pages by multimodal impressions; pages where multimodal `ctr` is far below
  `text_ctr` (image matches, click is lost) - route to `seo-images` / `ecommerce-optimization`.
- **Quick wins:** 3–5 striking-distance or low-CTR opportunities.

## Presentation

Lead with the summary line and trend direction. Then short tables for top queries,
top pages, and device split. End with a bulleted "Quick wins" list. State the window
and the ~3-day data lag.
