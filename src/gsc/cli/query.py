"""``gsc query`` command and the filter-string parser."""

from __future__ import annotations

import click

from ..client import GSCClient
from ..formatters import format_output
from .sites import get_client


def parse_filter(filter_str: str) -> dict:
    """Parse a ``dimension operator expression`` filter string into an API dict.

    The string is split into exactly three parts on whitespace, so the
    expression may itself contain spaces (e.g. ``query contains best shoes``).
    """
    parts = filter_str.split(None, 2)
    if len(parts) != 3:
        raise click.BadParameter(
            f"Filter must be 'dimension operator expression', got: {filter_str!r}"
        )
    dimension, operator, expression = parts
    return {
        "dimension": dimension,
        "operator": operator,
        "expression": expression,
    }


@click.command()
@click.argument("site_url")
@click.option("--start-date", required=True, help="Start date (YYYY-MM-DD).")
@click.option("--end-date", required=True, help="End date (YYYY-MM-DD).")
@click.option(
    "--dimensions",
    "-d",
    default="",
    help="Comma-separated dimensions (query,page,country,device,date,searchAppearance).",
)
@click.option(
    "--search-type",
    default=None,
    help="Search type: web, image, video, news, discover, googleNews.",
)
@click.option(
    "--filter",
    "filters",
    multiple=True,
    help="Filter as 'dimension operator expression'. Repeatable.",
)
@click.option(
    "--aggregation", "aggregation_type", default=None, help="auto, byPage, or byProperty."
)
@click.option("--row-limit", type=int, default=1000, help="Max rows (1-25000).")
@click.option("--start-row", type=int, default=0, help="Pagination start row.")
@click.option(
    "--data-state",
    default=None,
    help="all (include fresh) or final (default Google behaviour).",
)
@click.pass_context
def query(
    ctx: click.Context,
    site_url: str,
    start_date: str,
    end_date: str,
    dimensions: str,
    search_type: str | None,
    filters: tuple[str, ...],
    aggregation_type: str | None,
    row_limit: int,
    start_row: int,
    data_state: str | None,
) -> None:
    """Query Search Analytics for SITE_URL."""
    ctx.obj["site_url"] = site_url
    client = get_client(ctx)

    dimension_list = [d.strip() for d in dimensions.split(",") if d.strip()]
    parsed_filters = [parse_filter(f) for f in filters]

    body = GSCClient.build_query_body(
        start_date=start_date,
        end_date=end_date,
        dimensions=dimension_list or None,
        search_type=search_type,
        filters=parsed_filters or None,
        aggregation_type=aggregation_type,
        row_limit=row_limit,
        start_row=start_row,
        data_state=data_state,
    )

    response = client.query(site_url, body)
    rows = [_format_row(row, dimension_list) for row in response.rows]
    click.echo(format_output(rows, fmt=ctx.obj["format"]))


def _format_row(row, dimensions: list[str]) -> dict:
    out: dict = {}
    for name, value in zip(dimensions, row.keys):
        out[name] = value
    out["clicks"] = int(row.clicks)
    out["impressions"] = int(row.impressions)
    out["ctr"] = f"{row.ctr * 100:.2f}%"
    out["position"] = round(row.position, 1)
    return out
