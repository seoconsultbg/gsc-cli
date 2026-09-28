"""Render dicts / lists-of-dicts as JSON, a simple table, or CSV."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from tabulate import tabulate


def format_output(data: Any, *, fmt: str = "table") -> str:
    """Render ``data`` according to ``fmt`` (``json``, ``table``, or ``csv``).

    A single dict is coerced to a one-row list for table/CSV rendering. Empty
    input yields ``"No data."`` for tables and ``""`` for CSV.
    """
    if fmt == "json":
        return json.dumps(data, indent=2, default=str)

    rows = _as_rows(data)
    if fmt == "csv":
        return _format_csv(rows)
    return _format_table(rows)


def _as_rows(data: Any) -> list[dict]:
    if data is None:
        return []
    if isinstance(data, dict):
        return [data]
    return list(data)


def _format_table(rows: list[dict]) -> str:
    if not rows:
        return "No data."
    return tabulate(rows, headers="keys", tablefmt="simple")


def _format_csv(rows: list[dict]) -> str:
    if not rows:
        return ""
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue().strip("\r\n")
