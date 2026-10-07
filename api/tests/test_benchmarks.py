"""Tests for benchmark index lookup (signalscope.market_data.benchmarks)."""

from signalscope.market_data.benchmarks import get_benchmark_symbol


def test_known_markets_resolve_to_their_benchmark_index() -> None:
    assert get_benchmark_symbol("US") == "^GSPC"
    assert get_benchmark_symbol("SG") == "^STI"
    assert get_benchmark_symbol("HK") == "^HSI"
    assert get_benchmark_symbol("CN") == "000001.SS"
    assert get_benchmark_symbol("JP") == "^N225"
    assert get_benchmark_symbol("KR") == "^KS11"
    assert get_benchmark_symbol("TW") == "^TWII"


def test_unknown_market_returns_none() -> None:
    assert get_benchmark_symbol("ZZ") is None
