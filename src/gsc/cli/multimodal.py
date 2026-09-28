"""``gsc multimodal`` — ingest a Search Console UI export filtered to Web: multimodal.

The Search Analytics API has no multimodal search type (verified 2026-09-24,
discovery revision 20260923: ``type`` enum is WEB/IMAGE/VIDEO/NEWS/DISCOVER/
GOOGLE_NEWS and undocumented values return HTTP 400). The data is only reachable
through the Performance report's Export, so this command parses that export and
can join it with API ``web`` totals for the same dates to get the multimodal share.

API ``web`` equals the UI's "Web (text)" and excludes multimodal (verified on a
Bulgarian e-commerce property, 2026-06-22..2026-09-21: API 14,108 clicks / 468,429 impressions = UI
Web (text) exactly; UI Web (multimodal) 60 / 1,219 on top). Total = text + multimodal.
"""

from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path
from urllib.parse import unquote

import click

from ..client import GSCClient
from ..formatters import format_output
from .sites import get_client

# Export file per grouping. Queries are absent for multimodal: the query is an image.
_EXPORT_FILES = {
    "page": "Pages.csv",
    "country": "Countries.csv",
    "device": "Devices.csv",
    "date": "Dates.csv",
}
_API_PAGE_SIZE = 25000


def _read_export_file(source: Path, filename: str) -> tuple[str, str | None]:
    """Return (CSV text of ``filename``, Filters.csv text or None) from a zip, dir or CSV."""
    if source.is_file() and source.suffix.lower() == ".csv":
        filters = source.with_name("Filters.csv")
        return (
            source.read_text(encoding="utf-8-sig"),
            filters.read_text(encoding="utf-8-sig") if filters.exists() else None,
        )
    if source.is_file() and zipfile.is_zipfile(source):
        with zipfile.ZipFile(source) as zf:
            names = {Path(n).name.lower(): n for n in zf.namelist()}

            def _get(name: str) -> str | None:
                member = names.get(name.lower())
                return zf.read(member).decode("utf-8-sig") if member else None

            text = _get(filename)
            if text is None:
                raise click.BadParameter(
                    f"{filename} not found in {source.name}; available: {sorted(names)}. "
                    "Pass the CSV path directly if the export is localized."
                )
            return text, _get("Filters.csv")
    if source.is_dir():
        target = source / filename
        if not target.exists():
            raise click.BadParameter(f"{filename} not found in {source}")
        filters = source / "Filters.csv"
        return (
            target.read_text(encoding="utf-8-sig"),
            filters.read_text(encoding="utf-8-sig") if filters.exists() else None,
        )
    raise click.BadParameter(f"Not a GSC export zip, directory or CSV: {source}")


def _is_multimodal_export(filters_text: str | None) -> bool | None:
    """Whether Filters.csv records a multimodal search type; None when there is no Filters.csv.

    Matched on the value stem ("multimod" / "мултимод") because labels are localized.
    """
    if not filters_text:
        return None
    lowered = filters_text.lower()
    return "multimod" in lowered or "мултимод" in lowered


def _number(value: str) -> float:
    cleaned = value.strip().replace(" ", "").replace(" ", "").rstrip("%")
    if not cleaned:
        return 0.0
    # Localized exports may use a decimal comma ("3,44") with no thousands separator.
    if "," in cleaned and "." not in cleaned:
        cleaned = cleaned.replace(",", ".")
    else:
        cleaned = cleaned.replace(",", "")
    return float(cleaned)


def parse_export_rows(text: str, key_name: str) -> list[dict]:
    """Parse an export CSV positionally: key, clicks, impressions, CTR, position.

    Header names are ignored because Search Console localizes them to the UI language.
    """
    reader = csv.reader(io.StringIO(text))
    next(reader, None)
    rows: list[dict] = []
    for record in reader:
        if len(record) < 5 or not record[0].strip():
            continue
        clicks = int(_number(record[1]))
        impressions = int(_number(record[2]))
        rows.append(
            {
                key_name: record[0].strip(),
                "clicks": clicks,
                "impressions": impressions,
                "ctr": f"{(clicks / impressions * 100) if impressions else 0:.2f}%",
                "position": round(_number(record[4]), 1),
            }
        )
    return rows


def _fetch_text_by_page(
    client: GSCClient, site_url: str, start_date: str, end_date: str
) -> dict[str, tuple[int, int]]:
    """All pages' API ``web`` (= text-based) clicks/impressions, keyed by decoded URL."""
    totals: dict[str, tuple[int, int]] = {}
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
            totals[unquote(row.keys[0])] = (int(row.clicks), int(row.impressions))
        if len(response.rows) < _API_PAGE_SIZE:
            return totals
        start_row += _API_PAGE_SIZE


def _pct(part: float, whole: float) -> str:
    return f"{part / whole * 100:.2f}%" if whole else "n/a"


@click.command()
@click.argument("site_url")
@click.argument("export", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--by",
    "grouping",
    type=click.Choice(sorted(_EXPORT_FILES)),
    default="page",
    help="Which export table to read (default: page). Queries do not exist for multimodal.",
)
@click.option("--start-date", default=None, help="Export start date, for --compare.")
@click.option("--end-date", default=None, help="Export end date, for --compare.")
@click.option(
    "--compare",
    is_flag=True,
    help="Join with API web (= text-based) by page for the same dates (needs --by page + dates).",
)
@click.pass_context
def multimodal(
    ctx: click.Context,
    site_url: str,
    export: Path,
    grouping: str,
    start_date: str | None,
    end_date: str | None,
    compare: bool,
) -> None:
    """Parse a Performance export filtered to Web: multimodal for SITE_URL.

    EXPORT is the downloaded zip, its extracted folder, or one CSV from it.
    """
    text, filters_text = _read_export_file(export, _EXPORT_FILES[grouping])
    if _is_multimodal_export(filters_text) is False:
        click.echo(
            "Warning: Filters.csv does not show a multimodal search type. "
            "Re-export with Search type -> Web -> Multimodal.",
            err=True,
        )

    rows = parse_export_rows(text, grouping)

    if compare:
        if grouping != "page" or not (start_date and end_date):
            raise click.UsageError("--compare needs --by page plus --start-date and --end-date.")
        ctx.obj["site_url"] = site_url
        text_by_page = _fetch_text_by_page(get_client(ctx), site_url, start_date, end_date)
        for row in rows:
            text_clicks, text_impr = text_by_page.get(unquote(row["page"]), (0, 0))
            row["text_clicks"] = text_clicks
            row["text_impressions"] = text_impr
            row["mm_share_impressions"] = _pct(row["impressions"], text_impr + row["impressions"])
            row["text_ctr"] = _pct(text_clicks, text_impr)

    if grouping != "date":
        rows.sort(key=lambda r: r["impressions"], reverse=True)
    click.echo(format_output(rows, fmt=ctx.obj["format"]))
