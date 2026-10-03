---
name: gsc-opportunities
description: Find SEO quick wins in Google Search Console via the gsc CLI — striking-distance queries (position 11-20), low-CTR page-1 queries, and high-impression/low-click terms. Use when the user wants the highest-leverage opportunities to improve traffic.
allowed-tools: Bash(gsc *), WebFetch
---

# gsc-opportunities

Surface high-leverage quick wins. See `gsc-core` for the date convention, position
bands, and the expected-CTR-by-position table.

## Setup

Window: `END = today − 3`, `START = today − 31` (28 days, or as specified).

## Workflow

1. Queries with metrics:

   ```bash
   gsc --format json query "<SITE_URL>" --start-date <START> --end-date <END> \
       --dimensions query --row-limit 25000
   ```

2. (Optional) query + page pairs to attach the ranking page to each opportunity:

   ```bash
   gsc --format json query "<SITE_URL>" --start-date <START> --end-date <END> \
       --dimensions query,page --row-limit 25000
   ```

## Analysis

Classify each query (parse `position` as float, `ctr` from its `"x.xx%"` string):

- **Striking distance:** `position` 11–20 with high impressions — small ranking gains
  push to page 1. Highest priority. Within this bucket, rank a query that ALREADY
  earns clicks above a pure high-impression/zero-click one: a query Google has
  historically sent clicks for reconverts to page 1 faster and more reliably than
  one it has only ever shown. Split the striking-distance table into "has clicks
  (fast win)" first, then "impressions only" - and note which is which.
  AI-citation upside of the same move (Floyi Topical Authority Report 2026, 42
  topical maps, 535k top-20 positions, 355k AI citations): a page ranking 11-20
  for a query is cited in that query's AI Overview 12.9% of the time, 4-10 ->
  38.6%, 1-3 -> 60.7% (AI Mode 12.6 / 23.2 / 44.7%). Page 2 to top 10 roughly
  triples the citation odds, and breadth of coverage elsewhere on the site adds
  nothing on a query the page already ranks for - position does the work. Use it
  as the one-line justification when the client asks why striking distance beats
  "more content"; one vendor correlation study, so quote the order of magnitude,
  not the decimals. Ongoing AI-citation measurement stays with
  `ai-visibility-tracking`.
  Counterweight before promising AI upside for a specific page: Floyi measures
  citation RATE per query; page-level GSC data shows where AI impressions actually
  land, and there position explains little (iamveru.com, one travel site, 891 URLs:
  0.35% of AI impressions at avg pos 1-3, 69% at 4-10; a top-20 AI page averaged
  pos 35+). Top-3 pages often rank on brand/navigational queries that trigger no AI
  block. If the client has a Generative AI report export, run `gsc genai --compare`
  (see `gsc-core`) and check the page's `ai_lift` and intent first: pos 6 -> 2 is a
  click lever, not a proven AI-visibility lever.
- **Low CTR on page 1:** `position` 4–10 but `ctr` well below the expected band for
  its position (`gsc-core` table) — a title/meta rewrite opportunity. **Floor this
  bucket by sample first:** a low CTR on a handful of impressions is small-sample
  noise, not a title problem — one impression and no click reads as 0% CTR but means
  nothing. Require a minimum impression count (≈50 over a 28-day window as a rule of
  thumb; scale up for shorter windows) before a query earns a rewrite recommendation.
  Below the floor, low exposure ≠ weak title — set it aside rather than acting on it.
  Only low CTR that clears the floor AND the live-page check (below) is a real
  opportunity.
  Ground the diagnosis in the live SERP as well as in our page: pull the current
  top-10 snippets for the query (`dataforseo-research serp`, or Climby
  `climby_serp_benchmark` / `climby_rank_tracker_aio_gap` when the keyword is
  tracked) and note what the competing snippets carry - ratings, FAQ/sitelinks,
  year, price - and whether an AI Overview sits above the results. A CTR gap at a
  good position against rich competitor snippets or under an AIO is a
  format/feature gap (`seo-schema`, `ai-visibility-tracking` Step 6), not a
  wording gap, and no title variant closes it. (After M. Diggity's click-gap
  agent, 2026-09: GSC positions 3-20 with 500+ impressions/month, alarm floors
  CTR <3% at 3-5, <2% at 6-10, <1.5% at 11-20, then a top-10 snippet scrape ->
  meta rewrites. Use his floors only as an automation trigger on large
  properties; for judgment keep the expected-CTR band in `gsc-core`.)
- **High impressions / low clicks:** lots of impressions but very few clicks
  (combines deep position and/or weak CTR) — content or intent gap. The impression
  volume is the sufficiency floor here; the trap is the opposite one — treating
  machine-issued zero-click queries as a CTR failure (next section).

Rank within each bucket by impressions (opportunity size), EXCEPT striking distance,
where existing clicks outrank impressions (see above - historically-ranked queries
reconvert with less effort). Attach the ranking page from step 2 where useful.

## Machine-generated queries (filter before treating zero-click as a gap)

The "high impressions / low clicks" bucket is contaminated. LLMs and AI agents fan a
user's question out into many synthetic sub-queries and fire them at search; those
register as impressions with **zero clicks**, because no human ever saw the SERP.
The visible symptom is a widening gap between impressions and clicks - impressions
climbing, clicks flat - with CTR collapsing while real traffic is unchanged.

Do not report that as a CTR problem, and do not send a title rewrite after it. A
title rewrite cannot win a click from a query no human issued.

**Separate them:** in the zero/near-zero-click set, flag queries that look
machine-issued - unusually long and fully-formed natural-language questions,
stilted phrasing, near-duplicate variants of one another (often the same question
in two languages), and a sudden en-masse appearance rather than a gradual ramp.
Judge the pattern, not any single query; a long question query with clicks is a
normal question query, so run this filter only on the zero-click set.

**Then use them instead of discarding them.** This set is a free readout of what AI
systems want to know about the niche, and it is not available anywhere else:

1. Group by meaning (never optimise per synthetic query - there are hundreds).
2. Each group that the site does not answer well is a content-plan entry.
3. Route the recommendation to coverage and extractable chunks, not to titles/meta.

State the split in the report - "X of the Y zero-click queries look machine-issued;
treated as content-demand signal, not as CTR loss" - so the client does not read a
falling CTR line as a failure. When AI-surface visibility is the actual engagement,
hand off to `ai-visibility-tracking`; that skill owns the ongoing measurement.

This section is about agentic fan-out (synthetic, zero-click). The mirror case -
the conversational RESIDUE of human AI Mode sessions leaking in as ordinary rows
(pasted prompts, "yes go on", follow-ups), often WITH clicks, plus the anonymized
undercount - is owned by `gsc-ai-mode-detect`. Attribute a query to fan-out first
where the two overlap, so the same rows are not counted in both.

## Funnel bucketing: modifiers override topic (when clustering the query set)

When the deliverable is a clustered map of the query set (not just the four
opportunity buckets), classify intent BEFORE grouping by topic - the modifier
carries the intent even when the topic looks commercial:

| Modifier signals | Funnel stage |
|---|---|
| how to, DIY, tutorial, ideas, examples (BG: как да, съвети, примери) | TOFU |
| what is, types of, X vs Y concepts (BG: какво е, видове) | TOFU |
| best, top, review, alternative to (BG: най-добър, топ, ревю, алтернатива) | MOFU |
| pricing, buy, quote, custom, near me (BG: цена, купи, оферта, до мен) | BOFU |
| [brand] + product, free shipping, location modifiers | BOFU |

Tie-break with the "what would they click" test: if this searcher saw 10
results, which page type gets the click - a how-to (TOFU), a comparison (MOFU),
or a product/pricing page (BOFU)? Only after the stage is set, group by shared
topic/root term. Sorting the clusters BOFU-first turns the report into a
priority list by money, not by volume - and the BOFU/MOFU clusters are the
prompt-инвентар seeds for `ai-visibility-tracking`.

## Intent, weighted by CTR (do this before writing any title)

CTR is not only a problem signal. Across the query set of ONE page it is also a
readout of which framing users respond to: of two queries at a similar position,
the higher-CTR one is the wording that earns the click.

So when inferring a page's dominant intent, feed the model `query,ctr` pairs
(pulled from the step 2 query+page data, filtered to that page) and weight by CTR,
not by impressions. Impressions say what Google shows the page for; CTR says which
of those framings the user actually wanted. State the resulting intent in one
sentence and carry it into the rewrite - a title that matches high-impression
wording but not high-CTR wording is a downgrade.

Exclude the machine-issued set (previous section) before weighting - synthetic
queries have near-zero CTR by construction and will drag the intent toward noise.

**Stray-term vacuum** (added 2026-09-30, T. Kubaitis, SEO Fight Club). When a page
that is well tuned for its target barely shows for it, list its queries: if most
impressions sit on one off-topic term, a single incidental mention (a brand name in
a table cell, a tool name, a side product) may have pulled the page into a query with
demand but thin content. His page on "top SEO factors" got only "SEMrush" queries from
one data-source mention; removing that mention moved it up for the target. Fix: move
the stray term to a page that deserves it, then recheck in 2-4 weeks. Rare, but cheap
to check - one query export per page.

## Live-page grounding (MANDATORY before suggesting changes)

Before recommending any title/meta/heading change, WebFetch the affected pages
(top ~10-15 by opportunity) and extract the CURRENT title tag, meta description,
H1 and H2 list. Then:

- Never suggest adding something that is already there (keyword already in the H1,
  year already in the title, query already covered by an existing H2).
- If the current title is already strong, say so explicitly: "current title is
  effective, no change needed" — that is a valid and valuable finding.
- Title rewrites are shown side by side: current title -> suggested title, with a
  one-line reason (missing keyword / missing year / no hook / too long).
- "Too long" alone is not a reason (added 2026-09-29, after P. A. de Vera: a
  single-variable test on 900 pages with full-sentence, direct-response titles past
  60 characters - traffic +200%, 2,000 -> 9,000 visits, but real sales only +20%).
  Two rules follow: (1) front-load what qualifies the buyer (model, price, city,
  "buy"/"cost") so truncation cuts the hook, not the intent; (2) a hook title can
  pull readers who were never going to buy - judge a title change by leads /
  orders from GA4 or the CRM for those pages, not by clicks, and say so when you
  propose it.

Suggestions not grounded in the fetched page state are guesses — do not present them.

### Two title variants, sourced from click-earning vocabulary

Do not invent title vocabulary. Give TWO variants per page and let the client pick:

- **Variant A - literal.** Built ONLY from words that appear in that page's query
  set, prioritising the words carried by its highest-CTR queries. Add nothing that
  is not in the list. This is the safe option: it is provably wording Google already
  matches the page to and users already click.
- **Variant B - free.** A hook-first title, max 60 characters, using the same
  vocabulary as raw material but not bound to it. Here a clickable phrasing beats
  cramming in more keywords - one strong keyword plus a hook outperforms three
  keywords and no reason to click.

Present both against the current title, with the CTR-weighted intent sentence above
them so the choice is reasoned, not aesthetic.

## Question queries (listen to where Google already places you)

From the step 1 data, extract queries matching a question-word regex (client-side,
case-insensitive; cover the property's languages):

- EN: `^(how|what|why|can|does|do|is|are|when|which|where|who|should)\b`
- BG: `^(как|какво|защо|колко|кога|къде|кой|коя|кои|може ли|струва ли|трябва ли)\b`

Sort by impressions. These are questions Google is ALREADY trying to rank the site
for — demand discovered, not guessed. For each top question (after the live-page
grounding fetch): if the ranking page covers the same intent but lacks the phrasing,
add it as an H2/FAQ item; if the intent differs from the ranking page, it is a new
article candidate — route it to Group B below. Check intent by looking at what
actually ranks for the question, not by assumption.

## Commercial-intent queries (the money bucket)

From the step 1 data, bucket queries containing commercial markers (client-side,
case-insensitive; cover the property's languages):

- EN: `cost|price|pricing|services?|compan(y|ies)|near me|hire|quote|estimate|best`
- BG: `цена|цени|колко струва|фирма|фирми|услуг|майстор|оферта|оглед|най-добр`

Sort by clicks, then impressions. These queries convert — protect and strengthen.
For each: check it lands on a DEDICATED service/pricing page, not a blog post or
the homepage (use the step 2 query+page pairs). Queries without a dedicated page
are service-page candidates — flag them explicitly as the highest-commercial-value
gaps in the report.

## Long-tail routing (existing page vs new content)

From the step 1 data, extract queries with 5+ words. For each, match against the
site's pages (step 2 pairs; fallback: token overlap between query words and URL
slug words, ~30% threshold, mind hyphenated slugs and singular/plural variants).
Split into:

- **Group A - optimize existing page:** the query maps to a page. Check the page's
  fetched H2 structure — is the query already covered by a heading, or does it need
  a new H2/paragraph? Recommend the specific addition.
- **Group B - new content needed:** no page covers the topic. Deduplicate near-identical
  query variants into ONE brief ("what are the keys to X" == "what are the key to X"),
  then output an article brief only where impressions justify it. Route article
  briefs to seo-pipeline / question-gap conventions.

## Navigational-brand guardrail + thin-pool (do not chase unwinnable impressions)

(added 2026-09-13, "Clipy method" / gsc-intent-match teardown. Anti-false-positive layer over the buckets above.)

- **Navigational-brand queries are NOT a fixable mismatch - exclude them from the plan.** When someone types a product/brand name (a brand the searcher wants to GO to), a page of yours ranking page-1 at ~0% CTR is the brand owning its own SERP, not a title problem. A brand-review query (e.g. "agilitywriter review") sitting at #2 with ~0% CTR is winning as much as it ever will - **never recommend a title rewrite to chase a brand or spelling variant that already ranks.** These belong in a "Leave (no touch)" line, reported as a count, never as a confident action. This is the single most common false positive in a low-CTR list: high-impression navigational queries masquerading as fixable low-CTR pages. Detect them by intent (bare product/brand name, navigational) + the page already targeting the query.
- **Vanity-impression traps.** Page-1, big impressions, ~0% CTR, navigational intent = stop counting these impressions as a win and stop expanding content that only attracts them. They inflate the "opportunity" number without a reachable click.
- **Entity-first match when deciding fold vs separate (sharpens Group A/B).** Token overlap misclassifies because Google strips the capitalisation that marks a proper noun - "Content at Scale" (a product) reads as the words "content" + "scale" on a review of a different tool. Before routing a query to fold (Group A) vs separate page (Group B), ask entity-first: name what is searched, then judge whether the ranking page is about THAT exact thing. Page is about the searched entity but lacks the phrasing -> fold (add H2/FAQ). Page is about a different entity / a catch-all index (/blog/, /category/) caught it -> separate page. A specific article is never a "catch-all"; only the bare index is. When available, an LLM read of query+page content makes this call precise; token overlap is the fallback.
- **Thin-pool caveat (say it out loud).** GSC only shows queries you ALREADY rank for. When click-earning (non-navigational) intent is a small share of total impressions (rule of thumb: under ~25%), the convertible demand visible here is small BECAUSE the site hasn't built the pages yet - not because the opportunity is small. In that case pair this audit with demand discovery the site isn't capturing (question-gap / data-gap / Reddit + SERP), rather than implying the ceiling is low.

## Presentation

Four sections — Striking distance, Low-CTR page-1 (current title vs variants A/B),
High-impression/low-click, Long-tail routing (Group A / Group B) — each a table of
query, page, impressions, clicks, CTR, position, sorted by impressions. In striking
distance, put the "has clicks (fast win)" rows first, then "impressions only".
**Group striking distance by page before recommending anything.** One URL at 11-20 for
a dozen related queries is one action, not twelve: show one row per page, led by its
strongest query (clicks first, then impressions), with the sibling queries listed
under it. Otherwise a single page fills the table and pushes every other page off it.
For the top items give a concrete action grounded in the fetched page state. State
the window and ~3-day lag.
