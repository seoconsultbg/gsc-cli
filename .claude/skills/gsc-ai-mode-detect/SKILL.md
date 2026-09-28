---
name: gsc-ai-mode-detect
description: Detect and estimate the AI Mode / AI Overviews conversational residue that leaks into the GSC Performance report as ordinary query rows (pasted prompts, "yes go on", follow-ups), and quantify the anonymized undercount. Use when the user asks to track AI Mode traffic, find AI conversation queries in GSC, or measure how much of the query pool is hidden. Not for AI-answer visibility monitoring (ai-visibility-tracking) or agentic fan-out zero-click mining (gsc-opportunities).
allowed-tools: Bash(gsc *)
---

# gsc-ai-mode-detect

Google does not expose AI Mode at query level - the dedicated Search Generative AI
report (rolled out 2026-06-03) records only impressions inside generative features,
with no query attribution, and neither the Search Analytics API nor the BigQuery
bulk export returns generative-AI data. But the conversational RESIDUE of AI Mode /
AI Overviews sessions still lands in the normal Performance report as ordinary query
rows (confirmed by J. Mueller: it was always there). This skill isolates that
residue and, more importantly, quantifies how much of the pool is unreachable.

See `gsc-core` for the date convention, flags, and JSON shape. Read
[`references/ai-mode-query-patterns.md`](references/ai-mode-query-patterns.md)
before running - it holds the BG/EN/RU regex and the edge classes to disclose.

## What this is NOT (route elsewhere, do not double-count)

- **Agentic fan-out zero-click queries** - synthetic sub-queries an AI agent fires at
  search, registering as impressions with zero clicks. `gsc-opportunities` already
  owns these (its "Machine-generated queries" section) as a content-demand signal.
  This skill targets the RESIDUE of human AI Mode sessions, which often carries
  clicks. Where a query set overlaps both, attribute it to fan-out first.
- **AI-answer visibility / citation tracking** - whether models cite the brand.
  `ai-visibility-tracking` owns that ongoing measurement.

## Setup

Window: `END = today − 3`, `START` as specified (default `today − 31`). State the
window and the ~3-day lag in every output.

## Workflow

### 1. Pull the full query pool (bypass the 1000-row UI cap)

The report UI truncates to 1000 rows; the API does not. Page through in 25000-row
chunks until a page returns fewer than 25000 rows:

```bash
gsc --format json query "<SITE_URL>" --start-date <START> --end-date <END> \
    --dimensions query --row-limit 25000 --start-row 0
# then --start-row 25000, 50000, ... until short page
```

### 2. Server-side prefilter (Tier 1, high precision)

Pull only the high-precision residue directly with the Tier 1 regex from the
reference file (RE2, `includingRegex`):

```bash
gsc --format json query "<SITE_URL>" --start-date <START> --end-date <END> \
    --dimensions query --row-limit 25000 \
    --filter 'query includingRegex <TIER1_PATTERN>'
```

This is the safe, low-false-positive set. Do NOT server-side filter on Tier 2 bare
tokens (yes / ok / още / ещё) - they fire on real short queries.

### 3. Classify (regex is a prefilter, not a verdict)

Over the full pool from step 1, tag candidates into segments client-side:

1. **Prompt paste** - imperative openers (write/draft/generate/напиши/составь...).
2. **Confirmation / continuation** - "yes go on", "show me more", "покажи още",
   "продолжай"; multi-word = strong, bare token = weak.
3. **Follow-up / refinement** - "any other options", "what else", "другие варианты".
4. **Greeting / closer** - hi / thanks / здравей / спасибо (weak, Tier 2).
5. **Long fully-formed question** - gate on the near-zero-click set only (a long
   question WITH clicks is a normal query); overlaps fan-out → see gsc-opportunities.
6. **Gray zone** - conversational-looking but ambiguous between residue, long-tail,
   and ordinary. Do not force a call; mark as gray with a confidence note. (The
   source solves this with a fine-tuned xlm-roberta model; here Claude labels the
   gray zone from context, which is weaker - say so.)
7. **Excluded edge classes** - rank-tracker probes, agentic-harness prompts, pasted
   document chunks, "my location is", non-Latin/Cyrillic scripts. Count them as
   known-unmeasured, never silently fold them into a segment.

Report per-segment: row count, summed clicks, summed impressions, and 3-5 example
strings. Sort by clicks (residue with clicks is the real AI Mode footprint).

## The undercount ceiling (MANDATORY - the headline number)

Google anonymizes rare queries; conversational phrases are rare by nature, so a
large share of AI Mode never surfaces at query level at all. On the source author's
own BigQuery export (2026-08-11) **57.7% of impressions sat in the anonymized pool
over 59 days.** AI Mode clicks are tracked, but the queries behind them are almost
fully anonymized. Every extracted array is a hard undercount - state this at the
top of the report, not in a footnote.

**Estimate the property's own anonymized share** (do this - it is the most honest
number you can give):

```bash
# property total (no query dimension)
gsc --format json query "<SITE_URL>" --start-date <START> --end-date <END> \
    --aggregation byProperty
# vs the summed impressions of all query rows from step 1 (paginated)
```

`anonymized_share ≈ (property_total_impressions − Σ query_row_impressions) /
property_total_impressions`. This gap is the rare/anonymized pool (not only AI
Mode, but it is the ceiling on what any query-level method can ever see). Present it
as: "X% of impressions carry no surfaced query - the AI Mode residue below is a
lower bound within the remaining (100−X)%."

**Multimodal is NOT in this gap** (added 2026-09-24, verified on a Bulgarian e-commerce property): Web:
multimodal (Lens, Circle to Search, image upload) has no query text, but it is also
absent from the API `web` total (API `web` = UI "Web (text)"), so it neither inflates
nor explains `anonymized_share`. Do not attribute the gap to image queries. If you
report total Web visibility, add the multimodal export on top (`gsc multimodal`).

## Presentation

1. **Undercount banner first** - the property's anonymized share and the "lower
   bound" framing.
2. **Segment table** - the 7 segments (step 3), row/click/impression counts, examples.
3. **Edge classes not measured** - the explicit known-unmeasured list.
4. **So what** - if residue carries meaningful clicks, that is real AI Mode traffic
   to watch; route ongoing AI-surface engagement to `ai-visibility-tracking` and any
   demand signal in the fan-out set to `gsc-opportunities`. Do not recommend title
   rewrites off residue queries - no human chose that wording as a search.

Never present the extract as complete or as a traffic total. It is a labeled sample
under a hard anonymization ceiling.
