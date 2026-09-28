"""gsc-cli: Google Search Console CLI and SEO-analysis backend."""

from __future__ import annotations

from gsc.benchmarks import expected_ctr, is_ctr_opportunity, load_benchmarks

__version__ = "0.2.0"

__all__ = ["__version__", "load_benchmarks", "expected_ctr", "is_ctr_opportunity"]
