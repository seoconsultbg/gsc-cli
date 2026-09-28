"""``gsc genai`` — ingest a Search Console Generative AI report export (AI Overviews + AI Mode).

The Generative AI performance report (launched 2026-06-03) is UI/Export only: neither the
Search Analytics API nor the BigQuery bulk export returns it. It carries impressions only
(no clicks, CTR, position or queries), grouped by page, country, device or date, and the
export is capped at 1,000 rows.

``--compare`` joins the page table with API ``web`` for the same dates and computes an AI
lift index per page: the page's share of AI impressions divided by its share of organic
impressions, both inside the matched sample (method: iamveru.com, "Google AI visibility and
organic ranking data", 2026). Lift > 1 means the page takes more AI visibility than its
organic weight predicts. Tiny denominators produce absurd ratios, so rows below the
``--min-ai`` / ``--min-organic`` floors are marked ``qualified: false``.

Export layout (verified on a live property, 2026-09-28): Pages.csv, Countries.csv,
Devices.csv, Chart.csv (daily) and Filters.csv, each ``key,Impressions``; Filters.csv
records ``Search type,Web`` and the UI filter reads "Web (text)", so API ``web`` is the
matching organic denominator. The impressions column is still found by header name
(localized stems) with a positional fallback, in case a localized UI changes headers.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from urllib.parse import unquote

import click

from ..client import GSCClient
from ..formatters import format_output
from .multimodal import _number, _pct, _read_export_file
from .sites import get_client

_API_PAGE_SIZE = 25000
# Verified on a live export 2026-09-28: the daily table is Chart.csv, not Dates.csv.
_EXPORT_FILES = {
    "page": "Pages.csv",
    "country": "Countries.csv",
    "device": "Devices.csv",
    "date": "Chart.csv",
}
# Band labels follow the gsc-core benchmarks.
_BANDS = (("1-3", 3.0), ("4-10", 10.0), ("11-20", 20.0), ("21+", float("inf")))
_IMPRESSION_HEADERS = ("impression", "показван", "импресии", "zobrazen", "afișăr", "показы")


def _impressions_column(header: list[str]) -> int:
    """Index of the impressions column: by (localized) name, else by layout."""
    for index, name in enumerate(header):
        if any(stem in name.strip().lower() for stem in _IMPRESSION_HEADERS):
            return index
    # Impressions-only export: key, impressions. Performance layout: key, clicks, impressions.
    return 1 if len(header) <= 2 else 2


def parse_genai_rows(text: str, key_name: str) -> list[dict]:
    """Parse a Generative AI export CSV into ``{key_name, ai_impressions}`` rows."""
    reader = csv.reader(io.StringIO(text))
    header = next(reader, None) or []
    column = _impressions_column(header)
    rows: list[dict] = []
    for record in reader:
        if len(record) <= column or not record[0].strip():
            continue
        rows.append({key_name: record[0].strip(), "ai_impressions": int(_number(record[column]))})
    return rows


def _band(position: float) -> str:
    for label, upper in _BANDS:
        if position <= upper:
            return label
    return _BANDS[-1][0]


def _fetch_organic_by_page(
    client: GSCClient, site_url: str, start_date: str, end_date: str
) -> dict[str, tuple[int, int, float]]:
    """All pages' API ``web`` clicks, impressions and position, keyed by decoded URL."""
    totals: dict[str, tuple[int, int, float]] = {}
    start_row = 0
    while True:
        body = GSCClient.build_query_body(
            start_date=start_date,
            end_date=end_date,
            dimensions=["page"],
            search_type="web",
            row_limit=_API_PAGE_SIZE,
            start_row=start_row,
        )
        response = client.query(site_url, body)
        for row in response.rows:
            totals[unquote(row.keys[0])] = (
                int(row.clicks),
                int(row.impressions),
                float(row.position),
            )
        if len(response.rows) < _API_PAGE_SIZE:
            return totals
        start_row += _API_PAGE_SIZE


def _lift(ai_share: float, organic_share: float) -> float | None:
    return round(ai_share / organic_share, 3) if organic_share else None


def compare_rows(
    rows: list[dict],
    organic_by_page: dict[str, tuple[int, int, float]],
    min_ai: int,
    min_organic: int,
) -> tuple[list[dict], int]:
    """Join AI page rows with organic totals; return (matched rows, unmatched count).

    Shares are computed inside the matched sample, so both sides cover the same URLs.
    """
    matched: list[dict] = []
    for row in rows:
        organic = organic_by_page.get(unquote(row["page"]))
        if not organic or not organic[1]:
            continue
        clicks, impressions, position = organic
        matched.append(
            {
                **row,
                "organic_clicks": clicks,
                "organic_impressions": impressions,
                "organic_position": round(position, 1),
                "band": _band(position),
            }
        )
    ai_total = sum(r["ai_impressions"] for r in matched)
    organic_total = sum(r["organic_impressions"] for r in matched)
    for row in matched:
        ai_share = row["ai_impressions"] / ai_total if ai_total else 0.0
        organic_share = row["organic_impressions"] / organic_total if organic_total else 0.0
        row["ai_share"] = f"{ai_share * 100:.3f}%"
        row["organic_share"] = f"{organic_share * 100:.3f}%"
        row["ai_lift"] = _lift(ai_share, organic_share)
        row["qualified"] = (
            row["ai_impressions"] >= min_ai and row["organic_impressions"] >= min_organic
        )
    return matched, len(rows) - len(matched)


def band_summary(matched: list[dict]) -> list[dict]:
    """AI vs organic impressions per organic position band, with the band's lift."""
    ai_total = sum(r["ai_impressions"] for r in matched)
    organic_total = sum(r["organic_impressions"] for r in matched)
    summary: list[dict] = []
    for label, _ in _BANDS:
        members = [r for r in matched if r["band"] == label]
        ai = sum(r["ai_impressions"] for r in members)
        organic = sum(r["organic_impressions"] for r in members)
        summary.append(
            {
                "band": label,
                "urls": len(members),
                "ai_impressions": ai,
                "ai_share": _pct(ai, ai_total),
                "organic_impressions": organic,
                "organic_share": _pct(organic, organic_total),
                "ai_lift": _lift(
                    ai / ai_total if ai_total else 0.0,
                    organic / organic_total if organic_total else 0.0,
                ),
            }
        )
    return summary


@click.command()
@click.argument("site_url")
@click.argument("export", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--by",
    "grouping",
    type=click.Choice(sorted(_EXPORT_FILES)),
    default="page",
    help="Which export table to read (default: page). The report has no query table.",
)
@click.option("--start-date", default=None, help="Export start date, for --compare.")
@click.option("--end-date", default=None, help="Export end date, for --compare.")
@click.option(
    "--compare",
    is_flag=True,
    help="Join with API web by page for the same dates and add the AI lift index.",
)
@click.option(
    "--bands",
    is_flag=True,
    help="With --compare: output the per-position-band summary instead of page rows.",
)
@click.option("--min-ai", default=100, show_default=True, help="AI impressions floor.")
@click.option("--min-organic", default=1000, show_default=True, help="Organic impr. floor.")
@click.pass_context
def genai(
    ctx: click.Context,
    site_url: str,
    export: Path,
    grouping: str,
    start_date: str | None,
    end_date: str | None,
    compare: bool,
    bands: bool,
    min_ai: int,
    min_organic: int,
) -> None:
    """Parse a Generative AI report export (AI Overviews + AI Mode) for SITE_URL.

    EXPORT is the downloaded zip, its extracted folder, or one CSV from it.
    """
    text, _ = _read_export_file(export, _EXPORT_FILES[grouping])
    rows = parse_genai_rows(text, grouping)
    if len(rows) >= 1000:
        click.echo("Note: 1,000 rows = the export cap; the tail of the site is cut off.", err=True)

    if bands and not compare:
        raise click.UsageError("--bands needs --compare.")
    if compare:
        if grouping != "page" or not (start_date and end_date):
            raise click.UsageError("--compare needs --by page plus --start-date and --end-date.")
        ctx.obj["site_url"] = site_url
        organic = _fetch_organic_by_page(get_client(ctx), site_url, start_date, end_date)
        rows, unmatched = compare_rows(rows, organic, min_ai, min_organic)
        if unmatched:
            click.echo(
                f"Note: {unmatched} AI page(s) had no organic web impressions in the window "
                "and were left out of the shares.",
                err=True,
            )
        if bands:
            click.echo(format_output(band_summary(rows), fmt=ctx.obj["format"]))
            return

    if grouping != "date":
        rows.sort(key=lambda r: r["ai_impressions"], reverse=True)
    click.echo(format_output(rows, fmt=ctx.obj["format"]))
