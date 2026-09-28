---
name: gsc-core
description: Always-on reference for the gsc CLI — every command and flag, how to read the JSON output, the date convention, and SEO benchmarks used by all the gsc analysis skills.
user-invocable: false
---

# gsc-core

Shared reference for every `gsc-*` skill. The `gsc` binary is the only way these
skills reach Google Search Console — always call it with `--format json` and parse
the result. `--format` is **global** and comes *before* the subcommand.

## Date convention

GSC data lags ~2–3 days, so treat **end date = today − 3 days**. A "last 28 days"
window is `start = today − 31`, `end = today − 3` (both `YYYY-MM-DD`). Compute dates
from the current date before calling the CLI.

## Command reference

### Global options (before the subcommand)
- `--profile, -p NAME` — auth profile (default `$GSC_PROFILE`, else auto-detect by
  site URL, else `default`).
- `--format, -f {table|json|csv}` — always use `json` from skills.
- `--verbose, -v` — verbose errors.

### `gsc sites`
- `gsc --format json sites list` → `[{site_url, permission_level}, ...]`
- `gsc --format json sites get <SITE_URL>` → `{site_url, permission_level}`

### `gsc query <SITE_URL>`
Search Analytics. Options:
- `--start-date YYYY-MM-DD` (required), `--end-date YYYY-MM-DD` (required)
- `--dimensions, -d` — comma list: `query,page,country,device,date,searchAppearance`
- `--search-type` — `web|image|video|news|discover|googleNews`
- `--filter 'DIM OP EXPR'` — repeatable, AND-combined (e.g. `'query contains shoes'`,
  `'page equals https://x/p'`). Operators: `equals`, `notEquals`, `contains`,
  `notContains`, `includingRegex`, `excludingRegex`.
- `--aggregation auto|byPage|byProperty`
- `--row-limit N` (default 1000, max 25000), `--start-row N` (pagination)
- `--data-state all|final` — `all` includes fresh (incomplete) data.

Each row: `{<dimensions...>, clicks, impressions, ctr, position}`. `ctr` is a string
like `"3.45%"`; `position` is a float rounded to 1 decimal (lower = better).

**`--search-type` defaults to `web`, which excludes Discover.** Discover is a
separate surface with its own totals, so a site that gets meaningful Discover
traffic has a chunk of its performance invisible in every default query. Before
concluding anything about a period-over-period change on a content or news-ish
site, run the same window with `--search-type discover` and see whether the
movement is there instead. Two things make it easy to misread:

- **Discover has no queries.** It is not query-triggered, so `-d query` returns
  nothing useful; use `-d page` and `-d date`.
- **Discover traffic is spiky by nature.** Individual articles get picked up,
  spike for a few days and stop. A drop after a spike is the normal shape, not a
  regression - which means a "traffic collapse" that is entirely a Discover spike
  ending needs a different answer than a Search decline.

Same applies to `news`/`googleNews` on publisher properties.

**Web: multimodal is UI/Export only - the API cannot filter it** (added 2026-09-24;
Google Search Central blog "web-multimodal-in-sc", rolling out globally from 24.09.2026).
Search type -> Web now splits into **Text-based** and **Multimodal** (the query is an
image: Lens, Circle to Search, image upload, Chrome "Search this image"). Also shown in
the Generative AI features report. Verified 24.09: the API discovery doc (rev 20260923)
has no such `type` or `searchAppearance` value and guessed values return HTTP 400.
**API `web` = UI "Web (text)" and EXCLUDES multimodal** (verified on a Bulgarian e-commerce property,
2026-06-22..09-21: API 14,108 clicks / 468,429 impr = UI Web (text) to the unit; UI
`search_type=WEB` is itself labelled "Web (text)"; Web (multimodal) = 60 / 1,219 on
top, UI URL param `search_type=WEB-MULTIMODAL`). Consequences:
- **Every API-based analysis misses camera traffic** - it is additive, not hidden
  inside `web`. Total Web visibility = text (API) + multimodal (export).
- **No queries.** The UI shows "No query data for multimodal web search". It does not
  touch the query-anonymization gap (that gap is computed inside text-based `web`).
- **Getting it in:** in the UI pick Search type -> Web -> Multimodal, Export (zip),
  then `gsc multimodal` (below). Record the exact dates of the export.
- **Re-check the API** whenever the discovery revision changes; if a type appears, `--search-type` passes it straight
  through and the export step becomes unnecessary.

**Non-ASCII page URLs come back percent-encoded.** `-d page` returns Cyrillic (and
any non-ASCII) paths as `/%D0%B2%D1%81...`, while sitemaps, CMS exports and GSC UI
exports give the readable form. Always `urllib.parse.unquote()` BOTH sides before
joining page rows with any other URL list - otherwise those pages silently join as
0 clicks/0 impressions and look dead (a real pruning error seen in 09.2026). The
reverse trap: do not `quote()` a key that is already encoded when fetching it live
(double encoding returns a false 404).

**An empty or zero result is a failed probe until proven otherwise** (added 2026-09-25,
Claude Code Club (2026, Duncan Rogoff); the checks are this stack's own quirks). The API
answers a wrong question with `[]` or zeros, not an error. Before reporting "no data",
"0 clicks" or "page not in GSC", rule out the probe and say which checks passed:
- **Property form.** `sc-domain:x.com` covers every host and protocol; a URL-prefix
  property sees only its exact protocol + host + path (trailing slash, http vs https,
  www vs apex). Match the string from `gsc sites list`, look for a wider property, and
  write `page` filter URLs in that property's form.
- **Date window.** An end date inside the ~3-day lag, or `--data-state final` on recent
  days, gives empty or partial rows (see Date convention).
- **Filter encoding and values.** GSC stores non-ASCII page URLs percent-encoded (see
  the non-ASCII rule); if a readable Cyrillic `page` filter returns nothing, retry it
  with the encoded form before calling the page dead. `country`
  takes ISO 3166-1 alpha-3 (`bgr`, not `BG`); `device` takes `DESKTOP|MOBILE|TABLET`;
  regex operators use RE2. A wrong value is not rejected, it just matches nothing.
- **Dimension and surface fit.** `-d query` on `discover` returns nothing useful; a rare
  query under `equals` can sit inside the anonymized share and never appear; `web`
  excludes multimodal (above).
- **Permission.** `permission_level: siteUnverifiedUser` sees no data; check it with
  `gsc sites get` or switch `--profile`.

**Pull JSON, compute in code, then reason** (added 2026-09-26, Gadeev, "Промпт-инжиниринг
и работа с LLM", ch.12: a model reading a large table processes the visible part and
extrapolates silently). Every analysis skill follows this:
- Save the JSON and compute totals, impression-weighted position, group-bys, joins,
  deltas and counts with python or jq. Never do arithmetic over more than a handful of
  rows in the model's head.
- Report `rows_returned` for every pull next to its `--row-limit`. A pull whose row count
  equals the limit is truncated: paginate with `--start-row` or say the analysis covers
  only the top N rows.
- Any metric term with two reasonable readings (a "query" counted once or once per page,
  a "cannibalized" query by share OR by floor) gets one written definition before the
  numbers are computed; two runs that disagree point first to an ambiguous term.

### `gsc sitemaps <SITE_URL>`
- `list` → `[{path, last_submitted, last_downloaded, is_pending, is_sitemaps_index,
  type, warnings, errors, contents:[{type, submitted, indexed}]}, ...]`
- `get <FEEDPATH>` → one sitemap object
- `submit <FEEDPATH>` / `delete <FEEDPATH>` (need write access)

### `gsc inspect <SITE_URL> <INSPECTION_URL>`
URL Inspection → `{inspection_result_link, verdict, coverage_state, robots_txt_state,
indexing_state, page_fetch_state, google_canonical, user_canonical, last_crawl_time}`.
`verdict` is `PASS` / `NEUTRAL` / `FAIL`; `coverage_state` e.g. `"Submitted and
indexed"`, `"Crawled - currently not indexed"`, `"Discovered - currently not indexed"`.

### `gsc multimodal <SITE_URL> <EXPORT>`
Parses a Performance export filtered to Web -> Multimodal. `EXPORT` = the zip, its
extracted folder, or one CSV from it (use the CSV path for a localized export whose
file names differ). Columns are read by position, so BG/SK UI headers and decimal
commas work. Warns on stderr if Filters.csv does not show a multimodal search type.
- `--by page|country|device|date` (default `page`; there is no query table)
- `--compare --start-date D --end-date D` (page only) joins API `web` (= text-based)
  for the same window (URLs `unquote`d on both sides) and adds `text_clicks`,
  `text_impressions`, `text_ctr`, `mm_share_impressions` = mm / (text + mm).

Row: `{page|country|device|date, clicks, impressions, ctr, position, [compare fields]}`,
sorted by impressions (date keeps export order). Read `mm_share_impressions` as "how
much of this page's Web visibility is camera-driven"; a high share with `ctr` well
below `text_ctr` means the image wins the match but the page does not earn the click.

### `gsc genai <SITE_URL> <EXPORT>`
Parses an export of the **Generative AI performance report** (AI Overviews + AI Mode,
launched 2026-06-03; UI/Export only, not in the API or BigQuery). Impressions only - no
clicks, CTR, position or queries - and the export stops at 1,000 rows (stderr note when
hit). Same `EXPORT` forms and `--by page|country|device|date` as `multimodal`. Zip
layout verified on a live property 2026-09-28: Pages / Countries / Devices / **Chart.csv**
(daily - not Dates.csv) / Filters.csv, each `key,Impressions`; the report's search-type
filter defaults to "Web (text)", so API `web` is the matching denominator. Page rows sum
ABOVE the property total (page-level counting), as in the Performance report.
- `--compare --start-date D --end-date D` (page only) joins API `web` by page and adds
  `organic_clicks`, `organic_impressions`, `organic_position`, `band` (1-3 / 4-10 /
  11-20 / 21+), `ai_share`, `organic_share`, **`ai_lift`** = ai_share / organic_share,
  both computed inside the matched sample, and `qualified` (floors `--min-ai 100`,
  `--min-organic 1000`). AI pages with no organic web impressions are dropped (stderr).
- `--bands` (with `--compare`) outputs one row per position band: URL count, AI and
  organic impressions, their shares, band lift.

Row: `{page|country|device|date, ai_impressions, [compare fields]}`, sorted by AI
impressions. Read `ai_lift` only on `qualified: true` rows - small denominators give
absurd ratios. **Lift > 1** = the page takes more AI visibility than its organic weight:
study what it does (a directly liftable answer - how it works, limits, what next). **High
organic, lift near 0** is usually intent (navigational, brand, corporate pages where Google
shows no AI block), not a defect - do not "fix" it. `organic_position` is a page average
over all its queries, so bands are coarse; there is no query-level link. AI Mode
impressions are ALSO counted inside the normal Web totals, so AI is not additive the way
multimodal is. **Crawl blocks hit AI far harder than organic:** on a Bulgarian automotive site with Googlebot
blocked 04.08-03.09.2026 - organic impressions/day -42%, AI impressions/day -93% (AI/organic
ratio 16.6% -> 2.0% -> 17.0% after the fix). Run `--by date` next to API `web` by date: a
collapsing AI/organic ratio is an early crawl-access alarm. Method: iamveru.com "Google AI visibility and organic ranking data" (one
travel site, Jun-Jul 2026, 891 URLs: AI impressions 0.35% at pos 1-3, 69.2% at 4-10,
23.5% at 11-20, 6.9% at 21+; every top-100 AI URL was in the organic top 1,000).

## SEO benchmarks (use consistently across skills)

- **Position bands:** 1–3 top; 4–10 first page; **11–20 striking distance** (the
  prime quick-win zone — small gains can push to page 1); 21+ deep.
- **Expected CTR by position (web):** #1 ≈ 28%, #2 ≈ 15%, #3 ≈ 11%, #4 ≈ 8%,
  #5 ≈ 6%, #6 ≈ 4.5%, #7 ≈ 3.5%, #8 ≈ 3%, #9 ≈ 2.5%, #10 ≈ 2%. CTR materially below
  the band for its position = title/meta opportunity.
- **Quick wins:** striking-distance queries (pos 11–20) with high impressions; and
  page-1 queries (pos 4–10) with low CTR vs. the band.
- **Cannibalization:** one query served by ≥2 URLs each with meaningful impressions —
  they split authority and CTR.
- **Indexing health:** `coverage_state` containing "not indexed" on a top page is a
  priority issue. `last_crawl_time` older than ~30 days on an important page is stale.
  Caveat: the **"Crawled - currently not indexed"** bucket is frequently stale/wrong
  - a meaningful share of its URLs are actually indexed and drawing impressions. Do
  not read a rising count as deindexation; verify a sample via URL Inspection and
  track the *% actually indexed* trend (a falling % is the real alarm). The same
  staleness affects `google_canonical` mismatches and 404s on rarely-crawled pages.
  Method: `gsc-audit`.
- **Zero-click baseline (search-level, not per query)** (added 2026-09-24; iPullRank on Datos
  clickstream, 13.1 bn events, Oct 2024 - Dec 2025, read in full): **~47%** of Google searches
  end with no click, rising slowly (+2.6 pp in 15 months), and the loss comes out of **organic**
  clicks - paid share did not move. Only ~14-20% of clicks go to a site named in the query, so
  ~80%+ of clicks are discovery, i.e. winnable by ranking. Use the spread, never the average:
  countries 41% (Japan, Vietnam) to 54% (Philippines), US 49%; mobile runs 6-19 pp above desktop
  (US mobile 66%, UK 65%), the gap is widest in English-speaking markets and smallest in Asia;
  google.com zero-clicks more than the local ccTLD in the same country (new SERP features land
  on .com first). Reference-style queries lose most (Wikipedia ~31%, IMDb ~33% of would-be
  clicks absorbed) and destination-value sites least (Reddit ~14%, GitHub ~13%). Caveats before
  quoting it to a client: the panel is **94.5% desktop**, so headlines are desktop-weighted; it
  cannot attribute a lost click to AIO vs knowledge panel vs snippet; the demographic cut is one
  week and 72% male; Bulgaria and Slovakia are not in the country list. For a client, measure
  their own segment (GSC device + country split) instead of citing any national figure.

## Interpreting `position` (avoid these misreads)

- GSC position is a **search-log metric**: impression-weighted average across
  every query variant, device, location, and SERP feature where the site
  appeared. A rank-tracker number (DataForSEO live SERP, TopVisor, etc.) is a
  **synthetic probe**: one depersonalized SERP at one moment in one location.
  They routinely disagree (GSC 5 vs tracker 12) and both are correct - never
  present them as the same metric, and never "reconcile" them into one number.
- Weighted average hides bimodality: impressions at {1,1,1,7,7,7} average 4.0
  while the site never actually ranked 4. Before reporting "position ~4", check
  whether the daily/device breakdown is bimodal (feature slot vs organic slot,
  or two competing URLs).
- One bad reading is noise: a 5+ position drop in a single measurement is not a
  ranking change; treat it as real only after ~3 consecutive readings agree.
- Position without impressions is vanity: a query where a tracker shows top-10
  but GSC shows ≈0 impressions means nobody searches it that way (or the
  snippet never surfaces) - deprioritize before investing.
- Position no longer implies clicks where AI Overviews show: zero-click rates
  are ~54-64% on AIO queries and #1 CTR drops ~18-42%, while being cited inside
  the AI answer recovers clicks. Flag AIO presence when CTR looks broken at a
  good position.

Always state the analysis window and that data is GSC-delayed (~3 days).
