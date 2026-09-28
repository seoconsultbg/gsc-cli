"""Tests for the UI-export parsers behind ``gsc multimodal`` and ``gsc genai``."""

from __future__ import annotations

import zipfile
from pathlib import Path

from gsc.cli.genai import band_summary, compare_rows, parse_genai_rows
from gsc.cli.multimodal import _read_export_file, parse_export_rows


def test_multimodal_rows_localized_headers_and_decimal_comma() -> None:
    text = 'Страници,Кликвания,Импресии,CTR,Позиция\nhttps://x.bg/a,3,120,"2,5%","1,8"\n'
    rows = parse_export_rows(text, "page")
    assert rows == [
        {
            "page": "https://x.bg/a",
            "clicks": 3,
            "impressions": 120,
            "ctr": "2.50%",
            "position": 1.8,
        }
    ]


def test_genai_rows_impressions_only_with_spaced_thousands() -> None:
    text = "Top pages,Impressions\nhttps://x.bg/a,4 000\nhttps://x.bg/b,50\n"
    assert parse_genai_rows(text, "page") == [
        {"page": "https://x.bg/a", "ai_impressions": 4000},
        {"page": "https://x.bg/b", "ai_impressions": 50},
    ]


def test_genai_rows_find_impressions_column_by_name() -> None:
    text = "Page,Clicks,Impressions,CTR,Position\nu,3,1234,x,y\n"
    assert parse_genai_rows(text, "page") == [{"page": "u", "ai_impressions": 1234}]


def test_genai_zip_reads_chart_csv_for_dates(tmp_path: Path) -> None:
    export = tmp_path / "export.zip"
    with zipfile.ZipFile(export, "w") as zf:
        zf.writestr("Chart.csv", "Date,Impressions\n2026-06-22,1180\n".encode("utf-8-sig"))
        zf.writestr("Filters.csv", "Filter,Value\nSearch type,Web\n")
    text, filters = _read_export_file(export, "Chart.csv")
    assert parse_genai_rows(text, "date") == [{"date": "2026-06-22", "ai_impressions": 1180}]
    assert filters is not None and "Search type" in filters


def test_compare_rows_lift_floors_and_unmatched() -> None:
    rows = [
        {"page": "https://x.bg/a", "ai_impressions": 400},
        {"page": "https://x.bg/%D0%B1", "ai_impressions": 100},
        {"page": "https://x.bg/gone", "ai_impressions": 10},
    ]
    organic = {
        "https://x.bg/a": (10, 1000, 6.2),
        "https://x.bg/б": (50, 4000, 2.1),
    }
    matched, unmatched = compare_rows(rows, organic, min_ai=100, min_organic=1000)
    assert unmatched == 1
    by_page = {r["page"]: r for r in matched}
    # AI shares 80% / 20%, organic shares 20% / 80% -> lift 4 and 0.25.
    assert by_page["https://x.bg/a"]["ai_lift"] == 4.0
    assert by_page["https://x.bg/a"]["band"] == "4-10"
    assert by_page["https://x.bg/%D0%B1"]["ai_lift"] == 0.25
    assert by_page["https://x.bg/%D0%B1"]["band"] == "1-3"
    assert all(r["qualified"] for r in matched)


def test_band_summary_covers_every_band() -> None:
    matched, _ = compare_rows(
        [{"page": "a", "ai_impressions": 300}, {"page": "b", "ai_impressions": 100}],
        {"a": (1, 100, 5.0), "b": (1, 300, 15.0)},
        min_ai=100,
        min_organic=1000,
    )
    summary = {row["band"]: row for row in band_summary(matched)}
    assert list(summary) == ["1-3", "4-10", "11-20", "21+"]
    assert summary["4-10"]["ai_lift"] == 3.0
    assert summary["21+"]["urls"] == 0 and summary["21+"]["ai_lift"] is None
