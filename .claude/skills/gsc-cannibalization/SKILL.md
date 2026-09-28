---
name: gsc-cannibalization
description: Detect keyword cannibalization in Google Search Console via the gsc CLI — queries where multiple pages from the same site compete for the same term. Use when rankings are unstable or the user suspects pages are competing.
allowed-tools: Bash(gsc *)
---

# gsc-cannibalization

Find queries served by two or more URLs, where pages split authority, impressions,
and CTR. See `gsc-core` for the date convention and benchmarks.

## Setup

Window: `END = today − 3`, `START = today − 31` (28 days, or as the user specifies).

## Workflow

1. Pull query + page pairs:

   ```bash
   gsc --format json query "<SITE_URL>" --start-date <START> --end-date <END> \
       --dimensions query,page --row-limit 25000
   ```

2. (Optional, to narrow) re-run with `--filter 'query contains <term>'` for a
   specific keyword the user named.

## Analysis

Group the rows by `query` and collect the pages under each:

- A query is **cannibalized** when ≥2 pages each hold **≥ 5% of the query's impressions
  AND ≥ 10 impressions** in the window. Both conditions, fixed values, computed in a
  script over the saved JSON (see `gsc-core`, compute in code). Worked example: a query
  with 1,000 impressions split 850 / 90 / 60 is cannibalized (all three pass both);
  a query with 80 impressions split 70 / 6 / 4 is not (page 2 passes 5% but not 10
  impressions). State the thresholds in the report; if the user asks for a looser or
  stricter cut, change the numbers there, not the logic. (Added 2026-09-26: the earlier
  "≥ ~5% or a small floor" definition was an OR with no floor value, so two runs could
  classify the same query differently - Gadeev, ch.12.)
- For each cannibalized query, rank its competing pages by clicks/impressions and
  identify the likely "primary" (best position + most clicks).
- Estimate severity by total impressions at stake and how close the competing pages'
  positions are (closer = worse split).

Ignore queries where one page clearly dominates (others are negligible).

### Classify each hit before recommending anything

Type (severity is not one bucket):

| Type | Definition | Weight |
|---|---|---|
| Diffuse | 4+ pages share the query - heavy signal fragmentation | Most critical |
| Direct | 2-3 pages compete, none dominating | The working queue |
| Nominal | one page takes >90% of clicks | Minor; usually no action |

Stability (run the same pull for a longer window, e.g. 14d vs 90d):

- **Chronic** - present in both windows. These do not resolve themselves and
  are the real backlog.
- **New** - only in the short window; may be temporary reshuffling. Recheck
  before acting.
- **Fading** - only in the long window; likely already resolved. Verify and
  drop.

Prioritise with a simple composite score - severity type + stability +
impressions at stake + query frequency + number of competing pages - rather
than by impressions alone: a chronic diffuse query with modest impressions
beats a new nominal one with many. (Structure borrowed from a field
implementation, GOAUDIT 02.2026; weights there: severity 40-100, stability
0-30, impressions 0-30, frequency 0-20, page count 0-15.)

The most common root pattern on content+commerce sites: **articles competing
with category/service pages for commercial queries** - the fix is intent
differentiation plus internal links from the article to the money page, not
deletion.

### Onset cause: directive drift, not just content overlap

(added 2026-09-14, after Search Engine Journal "Ask an SEO: how do I identify
cannibalization problems, consolidate without loss of visibility", 09.2026)

The content-overlap pattern above assumes two pages genuinely about the same
thing. A second, easily-missed cause creates cannibalization on pages that
already existed and ranked fine for months, with no new content published: a
**change to crawl or index directives**. A plugin update or template deploy that
opens tags, internal search-result pages, category/facet pages, or
parameter/variant URLs in robots.txt or via `meta robots`; a canonical config
that stops declaring the official version (product variants each self-canonical,
or cross-canonicals dropped); a bulk `meta robots` flip - any of these lets
previously-suppressed duplicates re-enter the index and split the query with the
original.

**Diagnostic tell:** the onset lines up with a deploy / plugin update / config
change, NOT with a publish date - and the competing URLs are variant / tag /
search / facet / parameter URLs rather than distinct editorial pages. When you
see that, the fix is to **restore the directive** (re-close the page-type in
robots or noindex it, repair the canonicals so each variant points at the
official URL) - it is not a consolidate-vs-differentiate content decision.
Cross-check `recover-content` Level 0 Layer 3 ("position fell right after a CMS
edit" / "deindexed = robots/canonical/noindex") when the same change also
dropped the original's traffic.

**False positive - complementary pages are not cannibalization.** Two URLs can
legitimately take one keyword at different funnel stages (an informational guide
and a commercial/conversion page), and Google can serve whichever matches the
searcher's stage - so an even click split alone does not prove a problem. Use the
`latent-intent` Сценарий Е overlap test (below) to separate them: distinct
hidden-intent shares = keep both and differentiate; near-total overlap = genuine
duplication.

**Why this skill is GSC-native.** Detecting the same split from a rank tracker
(count how many of a site's URLs surface in the top 100 for a query) got more
expensive and less complete after Google removed the `&num=100` SERP parameter
(~Sept 2025): tools can no longer pull the top 100 in one request. GSC's
query+page report has no such ceiling and reports every URL that earned
impressions, so prefer it as the primary detector; reserve a rank tracker for
confirming the live SERP position of the URLs GSC already flagged.

## Presentation

A table per cannibalized query: the query, each competing page, and its
clicks/impressions/CTR/position. Sort by impressions at stake (highest first). For
the top offenders, recommend a fix: consolidate/redirect, differentiate intent, or
add internal links to the primary page. State the window and ~3-day lag.

To decide consolidate vs differentiate for a competing pair, use the
`latent-intent` skill (Сценарий Е): run both pages' main queries, compare the
hidden_intents sets - overlap above ~70-80% means true duplication
(consolidate + 301); distinct hidden-intent shares mean differentiate each
page under its own hypotheses instead of merging.

### Fourth resolution and the 60-day verification

(added 2026-08-23, after rampstackco/claude-skills, MIT; numbers are the author's heuristics, unverified)

- Beyond consolidate / differentiate / redirect, a fourth option: **noindex,follow + self-canonical** on the secondary page when it must exist for UX or business reasons (product variant, utility page) but should not rank. Keep its canonical pointing at itself - canonical and noindex do different jobs, and cross-canonical plus noindex sends mixed signals. Confirm in GSC after about a week that the noindex took; keep the page fully functional for users.
- After any resolution, monitor 60 days: canonical URL rank on the query (should stabilize and improve), merged/redirected URLs dropping out (expected), cluster impressions + clicks rising, zero internal links left to deprecated URLs.
- If the canonical has not improved by day 60, recheck in order: do the redirects fire (test 5 random old URLs); is another page on the site still competing for the query; is the canonical strong enough on its own against the top results.
