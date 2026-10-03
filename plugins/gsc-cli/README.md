# GSC CLI for Claude Code

Eleven skills that let Claude Code answer Google Search Console questions from your
own data: how a site is doing, what changed between two periods, which pages compete
for the same query, where the quick wins are, and why a page is not indexed. Each
skill runs the open-source `gsc` command on your machine, reads its JSON output and
reasons over it.

This is an unofficial tool. It is not affiliated with or endorsed by Google.

## Skills

| Skill | What it does |
| --- | --- |
| `gsc-analyze` | 28-day health check: totals, daily trend, top queries and pages, device split |
| `gsc-compare` | Two periods side by side: gainers, losers, new and lost queries and pages |
| `gsc-opportunities` | Striking-distance queries (positions 11-20), low-CTR page-1 queries, high-impression terms with few clicks |
| `gsc-cannibalization` | Queries where several of your pages compete for the same term |
| `gsc-audit` | Indexing audit of top pages plus sitemap health |
| `gsc-inspect` | URL Inspection for one page: verdict, coverage, crawl and index status, canonical |
| `gsc-ai-mode-detect` | Finds AI Mode and AI Overviews conversation residue in the query report and estimates the hidden share |
| `gsc-query` | Ad-hoc Search Analytics lookups by query, page, country, device or date |
| `gsc-sitemaps` | List, inspect, submit and delete sitemaps |
| `gsc-sites` | List the properties your account can see |
| `gsc-core` | Shared reference the other skills load: commands, flags, date convention, benchmarks |

Some skill files mention companion skills (for example `ai-visibility-tracking`) from
a larger private setup. They are optional; these skills work on their own.

## Requirements

- **Claude Code.** The skills need a local shell to run `gsc`. In claude.ai chat and
  Cowork they load, but there is no `gsc` to call there, so use them from Claude Code.
- **Python 3.11+ and the `gsc` command on your PATH:**

  ```bash
  uv tool install gsc-cli     # or: pipx install gsc-cli
  ```

- **An OAuth client for the Search Console API** (Google Cloud Console -> APIs &
  Services -> Credentials -> Desktop app). Point `GSC_CLIENT_SECRETS` at the
  downloaded `client_secrets.json`, then sign in once:

  ```bash
  gsc auth login
  gsc sites list
  ```

Service accounts and separate profiles for different clients are supported as well;
see the [main README](https://github.com/seoconsultbg/gsc-cli#readme).

## Install

In Claude Code:

```
/plugin marketplace add seoconsultbg/gsc-cli
/plugin install gsc-cli@seoconsult
```

Then ask in plain words, for example "how is https://www.example.com/ doing in
search" or "find keyword cannibalization on sc-domain:example.com".

## What runs and where your data goes

- The skills run one local program, `gsc`. They do not call any API themselves.
- `gsc` talks only to Google: the Search Console APIs on googleapis.com, and Google's
  OAuth endpoints when you sign in. It uses your own credentials, which stay on your
  machine in `~/.config/gsc/`.
- `gsc-opportunities` also fetches the pages it is about to comment on, using
  Claude's WebFetch, so its title and heading advice matches what is on the page
  today. Those are your own public pages.
- `gsc multimodal` and `gsc genai` read CSV or ZIP exports that you download from the
  Search Console interface yourself.
- Nothing is sent to SEO Consult or any other third party, and there is no telemetry.
- Only two commands change anything in Search Console: `gsc sitemaps submit` and
  `gsc sitemaps delete`. The `gsc-sitemaps` skill confirms with you before it runs
  either one. `gsc auth login` asks Google for read-write Search Console access
  because those two commands need it.

## License

MIT. Built and maintained by [SEO Consult](https://seoconsult.bg), an SEO agency in
Bulgaria. Source code, issues and the full CLI reference:
[github.com/seoconsultbg/gsc-cli](https://github.com/seoconsultbg/gsc-cli).
