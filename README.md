# gsc-cli

[![PyPI version](https://img.shields.io/pypi/v/gsc-cli.svg)](https://pypi.org/project/gsc-cli/)
[![Python versions](https://img.shields.io/pypi/pyversions/gsc-cli.svg)](https://pypi.org/project/gsc-cli/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Ruff](https://img.shields.io/badge/lint-ruff-261230.svg)](https://github.com/astral-sh/ruff)

**A fast, scriptable Google Search Console CLI** - pull Search Analytics, inspect
URLs, and manage sitemaps straight from your terminal, with clean `--format json`
output that pipes into any tool. It also powers a set of Claude Code SEO-analysis
skills.

> Built and maintained by **[SEO Consult](https://seoconsult.bg)**, a Bulgarian
> [SEO агенция](https://seoconsult.bg) that lives in Search Console data.

---

## Why gsc-cli

- **Everything as JSON.** `--format json` on any command → feed rankings, CTR, and
  impressions into scripts, notebooks, or LLM prompts without scraping the UI.
- **Search Analytics done right.** Query by `query`, `page`, `country`, `device`,
  or `date`, with repeatable AND-combined `--filter` expressions.
- **URL Inspection & sitemaps.** Check index coverage for any URL and list/submit/
  delete sitemaps.
- **Multi-profile auth.** OAuth2 *and* service accounts, with per-site
  auto-detection - juggle many client properties from one config.
- **Table / CSV / JSON** output for humans and machines alike.
- **The data the API leaves out.** Google Lens / Circle to Search traffic
  (Web: multimodal) and the Generative AI report (AI Overviews + AI Mode) exist
  only as UI exports. `gsc multimodal` and `gsc genai` parse those exports and
  join them with API numbers for the same dates.

## Install

```bash
pip install gsc-cli          # from PyPI
# or, for local development:
uv sync                      # create venv + install + register the `gsc` binary
```

## Quick start

```bash
export GSC_CLIENT_SECRETS=/path/to/client_secrets.json   # from Google Cloud Console
gsc auth login                                           # OAuth2 browser flow
gsc sites list                                           # confirm access

# Top queries for the last 28 days, as JSON:
gsc --format json query https://www.example.com/ \
    --start-date 2026-01-01 --end-date 2026-01-28 --dimensions query
```

`--format` is **global** and precedes the subcommand
(`gsc --format json query ...`). Filters use `'dimension operator expression'`,
e.g. `--filter 'query contains running shoes'`.

## Commands

| Command | What it does |
| --- | --- |
| `gsc auth` | `login`, `add-profile`, `list/remove-profile`, `status` |
| `gsc sites` | List and inspect verified properties |
| `gsc query` | Search Analytics (clicks, impressions, CTR, position) |
| `gsc inspect` | URL Inspection API - index/coverage verdict for a URL |
| `gsc sitemaps` | `list`, `get`, `submit`, `delete` |
| `gsc multimodal` | Parse a Web: multimodal export; `--compare` adds the camera share per page |
| `gsc genai` | Parse a Generative AI report export; `--compare` adds the AI lift index per page |

Run `gsc --help` or `gsc <command> --help` for the full flag reference.

## AI Overviews and AI Mode by page

The Generative AI report in Search Console shows how often each page appeared
inside AI Overviews and AI Mode. The API does not return it, so export it from the
UI (Performance -> Generative AI -> Export -> Download CSV) and run:

```bash
gsc genai https://www.example.com/ export.zip --compare     --start-date 2026-06-22 --end-date 2026-09-21
```

For every page you get its AI impressions next to its organic clicks, impressions
and average position, plus `ai_lift`: the page's share of AI impressions divided by
its share of organic impressions. Above 1, AI uses the page more than its organic
weight would suggest. Pages with fewer than 100 AI or 1,000 organic impressions are
marked `qualified: false`, because small numbers give silly ratios.

Add `--bands` to see how AI impressions split across position bands (1-3, 4-10,
11-20, 21+). On the sites we have checked so far, most AI visibility sits on pages
ranking 4-10, not in the top 3. Informational pages score high lift. Stock, deals
and dealer-locator pages score close to zero, because Google rarely shows an AI
answer for those searches.

`--by date` gives the daily series. Put it next to `gsc query --dimensions date`:
if the AI-to-organic ratio suddenly collapses, check whether Googlebot can still
reach the site. On one site, a firewall block cut organic impressions by 42% and AI
impressions by 93%.

Some skill files mention companion skills (for example `ai-visibility-tracking`)
from a larger private setup. They are optional; the `gsc-*` skills work on their own.

## Use with Claude Code

`gsc-cli` is the backend for a suite of Claude Code SEO skills (performance
overviews, cannibalization detection, quick-win opportunities, period compares,
indexing audits). The skills shell out to `gsc --format json` and reason over the
output. They ship as a Claude Code plugin in [`plugins/gsc-cli`](plugins/gsc-cli):

```
/plugin marketplace add seoconsultbg/gsc-cli
/plugin install gsc-cli@seoconsult
```

The plugin needs the `gsc` command on your PATH (`uv tool install gsc-cli` or
`pipx install gsc-cli`). See [CLAUDE.md](CLAUDE.md) for the architecture.

## Configuration

Profiles live in `~/.config/gsc/config.yaml` (override with `GSC_CONFIG_DIR`).
A command resolves its profile by precedence: explicit `--profile`/`$GSC_PROFILE`
→ the profile whose `sites` list contains the target URL → `default`. Full details
in [CLAUDE.md](CLAUDE.md).

## Contributing

Issues and PRs welcome. Lint/format with `ruff` (line-length 100):

```bash
uv run ruff check .
uv run pytest
```

## License

[MIT](LICENSE) - © 2026 [SEO Consult](https://seoconsult.bg).

---

<sub>Maintained by the team at <a href="https://seoconsult.bg">SEO Consult</a>. If gsc-cli
saves you time, a ⭐ on GitHub helps others find it.</sub>
