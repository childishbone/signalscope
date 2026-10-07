"""Tests for BenchmarkCache (signalscope.services.canslim), in complete
isolation from any database -- this is what verifies "fetched once per
market", since the API's own watchlist always includes real production
securities across several real markets and can't be used for a clean
call-count assertion."""

from datetime import date, timedelta
from decimal import Decimal

from signalscope.market_data.base import MarketDataProvider
from signalscope.market_data.types import Bar, EarningsHistory, FundHolding, SecurityMatch
from signalscope.services.canslim import BenchmarkCache


class _FakeProvider(MarketDataProvider):
    def __init__(self) -> None:
        self.call_count = 0

    def search_securities(self, query: str, limit: int = 8) -> list[SecurityMatch]:
        raise NotImplementedError

    def get_historical_bars(self, provider_symbol: str, period: str = "2y") -> list[Bar]:
        self.call_count += 1
        price = Decimal("100.0")
        return [
            Bar(
                trade_date=date(2025, 1, 1) + timedelta(days=i),
                open=price,
                high=price,
                low=price,
                close=price,
                adj_close=price,
                volume=1000,
            )
            for i in range(10)
        ]

    def get_earnings_history(self, provider_symbol: str) -> EarningsHistory:
        raise NotImplementedError

    def get_top_holdings(self, provider_symbol: str, limit: int = 10) -> list[FundHolding]:
        raise NotImplementedError


def test_fetches_once_per_country_even_when_asked_repeatedly() -> None:
    provider = _FakeProvider()
    cache = BenchmarkCache(provider)

    cache.closes_for_country("US")
    cache.closes_for_country("US")
    cache.closes_for_country("US")

    assert provider.call_count == 1


def test_fetches_separately_for_each_distinct_country() -> None:
    provider = _FakeProvider()
    cache = BenchmarkCache(provider)

    cache.closes_for_country("US")
    cache.closes_for_country("JP")
    cache.closes_for_country("US")

    assert provider.call_count == 2


def test_unsupported_country_returns_empty_without_calling_provider() -> None:
    provider = _FakeProvider()
    cache = BenchmarkCache(provider)

    closes, symbol = cache.closes_for_country("ZZ")

    assert closes == []
    assert symbol is None
    assert provider.call_count == 0
