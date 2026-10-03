# AI Mode residue query patterns (BG / EN / RU)

Paste-ready regex for isolating the conversational residue that AI Mode / AI
Overviews sessions leave in the GSC Performance report as ordinary query rows:
answer artifacts ("yes go on"), clarifying follow-ups, and whole pasted prompts.

All patterns are RE2 (the flavor GSC Custom regex and the Search Analytics API
`includingRegex` operator both use). Prefix `(?i)` for case-insensitive. These are
a **prefilter that builds a candidate set, never a verdict** - single common tokens
(more / още / ещё) fire on real short queries, so precision comes from the
multi-word phrases and the imperative-at-start anchors, not the bare words.

## Tier 1 - high precision (safe for server-side `--filter includingRegex`)

Multi-word continuations, confirmations and imperative prompt openers. These
strings almost never appeared in GSC before AI Overviews, so a match is a strong
AI-Mode-residue signal with few false positives.

```
(?i)(^(write|draft|generate|summari[sz]e|explain|act as|rewrite|translate|compare|give me|make me|list all|create a)\b|\b(yes go on|go on please|sounds good|show me more|tell me more|any other options|what else can|and then what|continue please|more examples|give me more)\b|^(напиши|състави|обясни|резюмирай|генерирай|направи ми|дай ми|сравни|преведи|изброй)\b|\b(покажи още|разкажи още|други варианти|какво още|а след това|продължи с)\b|^(напиши|составь|объясни|резюмируй|сгенерируй|сделай мне|дай мне|сравни|переведи|перечисли)\b|\b(покажи ещё|расскажи ещё|другие варианты|что ещё|а дальше|продолжай с)\b)
```

## Tier 2 - noisy (client-side only, treat as weak candidates)

Bare confirmations/greetings/follow-ups. High recall, low precision - never
filter server-side on these alone; collect, then let Tier 3 (model/Claude) judge.

- EN: `^(yes|ok|okay|sure|thanks|thank you|hi|hello|hey|more|continue|next|nope|no)$`
- BG: `^(да|добре|ок|благодаря|здравей|здрасти|още|продължи|не)$`
- RU: `^(да|хорошо|ок|спасибо|привет|здравствуй|ещё|еще|продолжай|дальше|нет)$`

## Edge classes the regex WILL miss (name them in the report, do not pretend coverage)

Per the source, pattern lists lose whole border classes - list them as
known-unmeasured rather than pretending the extract is complete:

- Rank-tracker position-check probes (look conversational, are not human AI Mode).
- Agentic-harness prompts (a tool talking to search, not a person in AI Mode).
- Pasted text chunks / documents dropped into the prompt box.
- `my location is ...` / location-disclosure lines.
- Any non-Latin, non-Cyrillic script (Tamil, Tanglish, Hinglish mix) - the source's
  own model needed synthetic training data in 8 languages to catch these; a regex in
  three scripts does not. If the property has traffic in other scripts, say the
  extract undercounts them specifically.

## Long fully-formed questions

Very long, grammatically complete natural-language questions are also residue, but
length alone is not a pattern - a long question WITH clicks is usually a normal
question query. Gate any length heuristic on the near-zero-click set only, and hand
the pattern (not the single row) to Tier 3 judgment. This overlaps with the
machine-issued fan-out set that `gsc-opportunities` already handles - see the
cross-reference in SKILL.md so the two are not double-counted.

Paste-ready length gate (10+ words; from BrightLocal's local AI study,
2026-09-16), to run only on the near-zero-click set as above:

```
^(?:\S+\s+){9,}\S+$
```

BrightLocal also suggests `(?i)(site:.*official|official.*site:)` to spot
`site:` searches aimed at a brand's official pages (Lily Ray reports ChatGPT
adding `site:` to its fan-outs). Treat any hit as machine-issued: it belongs to
the `gsc-opportunities` fan-out set, not to human AI Mode residue. It is
unverified whether such operator queries reach GSC at all, so an empty result
proves nothing.
