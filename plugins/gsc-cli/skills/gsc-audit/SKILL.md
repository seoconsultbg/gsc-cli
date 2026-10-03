---
name: gsc-audit
description: Indexing audit for a Google Search Console property via the gsc CLI — inspect top pages for index/coverage issues and check sitemap health. Use when the user asks why pages are not indexed or wants a technical/indexing health check.
allowed-tools: Bash(gsc *)
---

# gsc-audit

Audit indexing health: inspect the most important pages and review sitemaps. See
`gsc-core` for verdict/coverage meanings and benchmarks.

## Setup

Window for finding top pages: `END = today − 3`, `START = today − 31`.

## Workflow

1. Find the top pages by clicks/impressions:

   ```bash
   gsc --format json query "<SITE_URL>" --start-date <START> --end-date <END> \
       --dimensions page --row-limit 25
   ```

2. Inspect each top page (the URL Inspection API is rate-limited — keep the set
   small, ~10–20):

   ```bash
   gsc --format json inspect "<SITE_URL>" "<PAGE_URL>"
   ```

3. Check sitemap health:

   ```bash
   gsc --format json sitemaps list "<SITE_URL>"
   ```

## Analysis

- **Per page:** `verdict`, `coverage_state`, `robots_txt_state`, `page_fetch_state`,
  and whether `google_canonical` ≠ `user_canonical`. Flag any top page whose
  `coverage_state` contains "not indexed", or with a fetch/robots problem, or a
  `last_crawl_time` older than ~30 days (stale).
- **Sitemaps:** per content type compare `submitted` vs `indexed`; flag
  `errors > 0`, big indexed gaps, `is_pending`, or stale `last_downloaded`.

## "Crawled - currently not indexed" is unreliable — verify before reporting

Never report a growing "Crawled - currently not indexed" count as deindexation on
its face. A significant share of URLs in that bucket are actually INDEXED and
receiving impressions (AJ Kohn, tracked 2x/month across all 1000 examples; holds
even on <100-page sites, where 10-15 are typically live). Glenn Gabe attributes
much of it on large sites to reporting lag on URLs that still rank in the top ~1000.

- **Verify a sample, don't trust the label.** Take URLs from the bucket and run
  `gsc inspect` on each; `verdict: PASS` / coverage "Submitted and indexed" - or the
  URL showing impressions in a `query --dimensions page` pull - means it is actually
  indexed despite the bucket. Compute **% actually indexed** of the sample.
- **The real signal is the TREND of that %, not the raw count.** Record
  `% actually indexed` on a schedule (~2x/month). A FALLING % (e.g. 97% -> 70%) is
  the alarm - that is when pages genuinely start dropping out; a rising raw count
  with a stable high % is mostly reporting noise. Without the periodic check you
  miss the moment real deindexation begins.
- **Same staleness hits `google_canonical` mismatches and 404s,** especially
  rarely-crawled pages - verify those with `gsc inspect` too before acting, and
  confirm freshness via `last_crawl_time`.
- **Sampling caveat.** GSC caps the report at 1000 examples, exposes no direct API
  to it, and keeps only ~3 months of history - so persist results yourself and treat
  the 1000 as a sample whose representativeness is unproven on very large buckets.
  gsc-cli makes the loop cheap: pull candidate URLs -> `gsc inspect` each -> store
  `verdict` + date -> chart the % over time (beats a manual ~7-min/1000 pass or a
  browser extension).

## Presentation

Open with a count of top pages indexed vs not. Table of problem pages with their
coverage state and the likely cause. Then a sitemap-health table. End with a
prioritized fix list (indexing blockers first). State the window and ~3-day lag, and
note URL Inspection rate limits.
