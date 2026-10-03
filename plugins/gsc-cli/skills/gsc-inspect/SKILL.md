---
name: gsc-inspect
description: Inspect a single URL in Google's index via the gsc CLI URL Inspection API — verdict, coverage state, crawl/index status, and canonical. Use when the user asks whether a specific page is indexed or why it is not.
allowed-tools: Bash(gsc *)
---

# gsc-inspect

Inspect one URL's index status. See `gsc-core` for verdict/coverage meanings.

## Usage

```bash
gsc --format json inspect "<SITE_URL>" "<INSPECTION_URL>"
```

→ `{ inspection_result_link, verdict, coverage_state, robots_txt_state,
indexing_state, page_fetch_state, google_canonical, user_canonical, last_crawl_time }`.

The `INSPECTION_URL` must belong to the property (`SITE_URL`).

## Workflow

1. Run the inspect call for the URL.
2. Read `verdict` (`PASS`/`NEUTRAL`/`FAIL`) and `coverage_state`.
3. If not indexed, look at `robots_txt_state`, `page_fetch_state`, `indexing_state`,
   and whether `google_canonical` differs from `user_canonical`.
4. If `google_canonical` is on a **different, unrelated domain**, suspect a broken
   render before a hijack (added 2026-09-28, J. Mueller via SEJ 18.09.2026): pages
   that served a generic JavaScript error shell to Googlebot look identical to every
   other site showing that shell, so Google folds them together and may pick any of
   those URLs. Ask for the GSC live URL test screenshot / rendered HTML; the fix is
   the render error, not the canonical tag.

## Presentation

State plainly whether the page is indexed and, if not, the most likely reason
(blocked by robots, fetch error, canonical points elsewhere, "Discovered/Crawled –
currently not indexed"). Note `last_crawl_time`; if older than ~30 days call it
stale. Offer the `inspection_result_link` for the full report in GSC. Note this API
is rate-limited, so inspect URLs sparingly.
