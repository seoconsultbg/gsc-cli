---
name: gsc-compare
description: Compare two time periods of Google Search Console data via the gsc CLI — gainers and losers, plus new and lost queries and pages. Use when the user asks what changed, period-over-period, or whether a change helped.
allowed-tools: Bash(gsc *)
---

# gsc-compare

Compare two equal-length windows and surface what moved. See `gsc-core` for the date
convention and benchmarks.

## Setup

Default to two adjacent 28-day windows ending at `today − 3`:

- **Current:** `CUR_END = today − 3`, `CUR_START = today − 31`.
- **Previous:** `PREV_END = today − 32`, `PREV_START = today − 60`.

Honour any explicit dates the user gives; keep both windows the same length.

## Workflow

Run each query for both windows (current and previous).

1. Queries, current and previous. Pull the **full** row set of each window: page with
   `--row-limit 25000 --start-row 0`, then `--start-row 25000, 50000, ...` until a page
   comes back shorter than the limit.

   ```bash
   gsc --format json query "<SITE_URL>" --start-date <CUR_START> --end-date <CUR_END> \
       --dimensions query --row-limit 25000 --start-row 0
   gsc --format json query "<SITE_URL>" --start-date <PREV_START> --end-date <PREV_END> \
       --dimensions query --row-limit 25000 --start-row 0
   ```

2. Pages, current and previous (same pattern with `--dimensions page`).

**New / Lost need the full set on both sides.** With a capped pull, a query at row 1001
last period and row 950 now shows up as "New" although nothing changed in search: the
bucket reports where the cutoff fell. If you cap anyway (a quick look), rename the
buckets to "entered / left the top N" and state N, and report `rows_returned` per window
next to the limit. A window whose `rows_returned` equals the limit is truncated.

## Analysis

Join current vs. previous on the dimension key:

- **Gainers / losers:** largest absolute and percent change in clicks (and
  impressions). Note position deltas (negative = improved).
- **New:** keys present now, absent before.
- **Lost:** keys present before, absent now (or dropped to ~0 clicks).

Do this for both queries and pages.

**Read the shape of a loser before naming the cause** (added 2026-09-11, after
M. Diggity's GSC decay agent; his two markers, extended):

| Shape | Read it as | Route |
|---|---|---|
| Clicks down 20%+ AND position worse | ranking loss | `recover-content` triage (Level 0 first when many pages move together) |
| Impressions flat or up, clicks down, position flat | a SERP feature / AI Overview absorbed the clicks, or a competitor won the snippet | live SERP check on the query (`climby_rank_tracker_aio_gap`, `dataforseo-research serp`); `ai-visibility-tracking` Step 6 - not a title rewrite |
| Impressions down, position flat | demand fell (check YoY / seasonality) or the query set narrowed | `recover-content` Level 0, Layers 1-2 |
| Clicks split between two URLs on one query | cannibalization | `gsc-cannibalization` |

For decay detection (as opposed to "what changed after X") compare two 90-day
windows instead of 28-day ones - weekly noise and single-feature flips wash out,
and the 15-25% decay thresholds in `recover-content` are defined on 90d.

**Same-domain pairs when the question is "what did this update reward"** (added
2026-09-22, after a published placebo-controlled update-analysis method,
Charles_SEO on X, Aug 2026 spam update - the method is borrowed, that study's
own factor findings are one dataset at C-class confidence and are NOT carried
over here):

When the user asks what an algorithm update rewarded or punished at page level,
do not read it off a site-wide aggregate and do not compare against competitors.
Pair two pages **on the same site** that serve an overlapping query cluster and
moved in opposite directions in the same window - one dropped, the other held or
gained. Every domain-level factor (authority, trust, backlink profile, brand,
hosting, technical stack, site-wide templates) is held constant by construction,
so whatever remains in the delta is page-level by definition. Build the pairs
from the `--dimensions query,page` pull, grouped by query.

Two limits, both mandatory to state when reporting from such a pair:

- **The design is blind to everything domain-level.** Domain factors are constant
  *by construction*, so this comparison can never say anything about authority,
  trust or site-wide signals. "Authority did not matter here" read out of a
  same-domain pair is an artifact of the pairing, not a finding - never report it
  as one.
- **It selects on the outcome.** You chose the pair *because* the pages moved, so
  the result describes what correlates with the move; it does not establish
  cause. For causal claims about an edit, route to `signalforge` (pre-registered
  measurement contract), not here.

Before attributing a same-domain pair to the update at all, rule out
`gsc-cannibalization`: two pages of one site splitting one query may simply be
competing with each other.

**Turbulence window.** When the compared windows straddle a known site change
(relaunch, major content update, migration), flag deltas from the first ~2
weeks after the change as provisional: fresh and updated pages go through a
volatile test period (position rotation / explore-style click sampling), and
GSC average position over those days mixes rotating intraday states. Prefer
re-running the comparison with the turbulence window excluded or shifted
before declaring the change won or lost; add `--dimensions date` granularity
to see whether a delta is a trend or a few noisy days.

**Position is stochastic - compare medians, not points** (added 2026-09-22, from
the "SEO с AI-агентами" intensive, Alexey Chekushin, day 3: his corrections to an
LLM's own first-pass plan for this exact task):

- **Never compare position on date A against position on date B.** Positions rotate
  even with nothing changed. Take the **median over each window** (7-14 days is enough
  for the shock-detection mode below; keep 90d for decay).
- **Compute the deltas with a script, not in the model's head.** Arithmetic over
  hundreds of rows is where silent errors enter. Same rule as `gsc-core`: pull JSON,
  compute, then reason.
- **Two modes.** *Date known* - compare the windows either side of it. *Date unknown* -
  find the **shock day**: the day the core-wide median moved sharply. Then check what
  happened after: if it came back within the tuning days it was turbulence, not an
  update.
- **Classify per query with thresholds, not with ±1.** Buckets: grew / fell / stable /
  new (appeared in the top) / lost. The thresholds are **not symmetric across the
  range** - a 3 → 7 move matters more than 2 → 8 - and **low-frequency queries are
  noisier than high-frequency ones**, so a band that reads as movement on a head term
  is noise on a tail term. Aggregate to top-3 / top-10 / top-30 counts plus
  frequency-weighted visibility; do not report "N queries moved" without weighting.

**What moves together: the pattern read** (same source; the corrections matter more
than the list, because a model asked to do this will produce the naive version):

| Pattern | The naive version an LLM will give you | What actually identifies it |
|---|---|---|
| Host-level | "many query types moved one way" | a **uniform** move across the whole host, with **no segment** carrying it. If one segment explains most of it, it is not host-level |
| Section-level | "one folder / one page template" | also, and often, **one word** in the query - the cut can be lexical rather than structural, so test segments by query token as well as by URL path |
| Cannibalization / URL swap | "pages swapped, so the site dropped" | a swap of which URL answers **need not lower positions at all**. Confirm the drop separately before attributing it (`gsc-cannibalization`) |
| Frequency band | "high-frequency loosened" | see the threshold rule above - tail volatility is the base rate, not a finding |
| Commercial vs informational | "detect commerciality from the words in the query" | word-spotting does not determine commerciality. Use a **stored, measured** commerciality score if you have one, and check whether the **SERP's own intent changed** (the result-type mix on that query) - the site may not have moved at all while the query did |

A model with no skill behind it produces junior-level work on this task
specifically - it reasons from publicly available patterns rather than from what
you have already observed on this site. Write the checklist it must walk (indexation,
links, competitors, intent shift, own edits) into the skill; do not expect it from
the weights.

## Brand PPC pause test (does paid brand search add clicks, or just buy organic ones?)

(added 2026-09-24. Method prompted by a practitioner claim - Ramon Eijkemans, a finance client, "99% of
brand traffic moved to organic" via geo-randomised pausing of brand ads; the case itself is not published,
treat the 99% as one anecdote. Context: iPullRank/Datos 2026 found brand clicks are ~1.3x more likely to be
paid than non-brand, i.e. defensive bidding is common and often unmeasured.)

Do not switch brand campaigns off nationally and compare months - seasonality and brand demand swamp the
signal. Run a geo holdout:
1. **Split regions, not time.** Assign matched regions (similar brand search volume) to test (brand ads
   paused) and control (ads on); randomise the assignment. Alternating on/off by region on a schedule works
   too, but balance it across weekdays or day-of-week effects masquerade as the result.
2. **Measure total brand clicks and conversions, paid + organic, per region.** GSC has no sub-country geo,
   so region-level organic comes from GA4 (landing sessions by region, organic channel, brand landing pages)
   and paid from Ads geo reports. Use GSC brand-query clicks by country only as a sanity check.
3. **Read incrementality:** (paid + organic in test) vs (paid + organic in control), normalised to the
   pre-test baseline of each region set. Recovery close to 100% = the brand ads were buying clicks you
   would get anyway.
4. **Check the SERP before deciding.** Auction Insights and a live SERP for brand terms in test regions:
   if competitors (or affiliates, resellers, aggregators) start bidding on the brand, the paid slot is
   defensive and pausing hands them the top of your own results. AI Overviews or a thin brand SERP also
   change the answer.
5. **Keep a floor.** Even at high recovery, many keep brand ads on for sitelink control, new offers and
   trademark monitoring; in regulated niches (finance) check brand compliance obligations first.
The claim that geo rotation "blinds competitors" is marketing, not measured - do not promise it.

## Presentation

For queries and for pages, show: top gainers, top losers, notable new, notable lost
(small tables with before → after clicks and position delta). Open with a one-line
net summary (total clicks Δ and direction). State both windows and the ~3-day lag.
