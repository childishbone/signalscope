import os

import pytest

from signalscope.market_data.yahoo import YahooProvider

pytestmark = pytest.mark.skipif(
    os.environ.get("SIGNALSCOPE_NETWORK_TESTS") != "1",
    reason="Set SIGNALSCOPE_NETWORK_TESTS=1 to run tests that call the real Yahoo API",
)


@pytest.fixture()
def provider() -> YahooProvider:
    return YahooProvider()


def test_search_returns_only_supported_exchanges(provider: YahooProvider) -> None:
    results = provider.search_securities("Toyota")
    assert results, "expected at least one result"
    for match in results:
        assert match.exchange_code.startswith(("X", "ARCX"))  # sanity: no PNK/IOB/FRA leaked


def test_search_finds_tokyo_toyota(provider: YahooProvider) -> None:
    results = provider.search_securities("Toyota")
    assert any(m.provider_symbol == "7203.T" for m in results)


def test_historical_bars_have_no_missing_prices(provider: YahooProvider) -> None:
    bars = provider.get_historical_bars("AAPL", period="6mo")
    assert len(bars) > 100
    for bar in bars:
        assert bar.high >= bar.low
        assert bar.close > 0
