"""Benchmark index symbols for CANSLIM letter M (market direction), one
per market this app supports, keyed by Security.country (ISO alpha-2).
"""

from __future__ import annotations

BENCHMARK_INDEX_BY_COUNTRY: dict[str, str] = {
    "US": "^GSPC",
    "SG": "^STI",
    "HK": "^HSI",
    "CN": "000001.SS",
    "JP": "^N225",
    "KR": "^KS11",
    "TW": "^TWII",
}


def get_benchmark_symbol(country: str) -> str | None:
    """The benchmark index ticker for a market, or None if unsupported."""
    return BENCHMARK_INDEX_BY_COUNTRY.get(country)
