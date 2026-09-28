"""Loader for the bundled open SEO benchmarks dataset.

The dataset (``gsc/data/seo-benchmarks.json``) is CC BY 4.0 — attribution to the
source is required when you reuse it. See ``data/README.md`` in the repository.
"""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from typing import Any


@lru_cache(maxsize=1)
def load_benchmarks() -> dict[str, Any]:
    """Return the bundled SEO benchmarks dataset as a dict."""
    data = resources.files("gsc.data").joinpath("seo-benchmarks.json").read_text("utf-8")
    return json.loads(data)


def expected_ctr(position: int) -> float | None:
    """Expected organic CTR (fraction) for a 1-based ranking ``position``.

    Returns ``None`` for positions outside the benchmarked 1-10 range.
    """
    values = load_benchmarks()["ctr_by_position"]["values"]
    return values.get(str(position))


def is_ctr_opportunity(position: int, actual_ctr: float, tolerance: float = 0.7) -> bool:
    """True if ``actual_ctr`` is materially below the expected band for ``position``."""
    expected = expected_ctr(position)
    return expected is not None and actual_ctr < expected * tolerance
