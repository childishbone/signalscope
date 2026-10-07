"""The provider-agnostic interface the rest of the app depends on.

Nothing outside market_data/ should import yfinance (or any other provider
library) directly. Swapping or adding a provider means writing a new class
here, not touching the callers.
"""

from abc import ABC, abstractmethod

from signalscope.market_data.types import Bar, EarningsHistory, FundHolding, SecurityMatch


class MarketDataProvider(ABC):
    @abstractmethod
    def search_securities(self, query: str, limit: int = 8) -> list[SecurityMatch]:
        """Search for securities, restricted to markets this app supports."""

    @abstractmethod
    def get_historical_bars(self, provider_symbol: str, period: str = "2y") -> list[Bar]:
        """Daily OHLCV bars, oldest first. Incomplete bars are excluded."""

    @abstractmethod
    def get_earnings_history(self, provider_symbol: str) -> EarningsHistory:
        """Quarterly and annual EPS history, oldest first. Empty lists if
        the provider has none (common for ETFs, and for thinner-coverage
        non-US tickers)."""

    @abstractmethod
    def get_top_holdings(self, provider_symbol: str, limit: int = 10) -> list[FundHolding]:
        """An ETF/fund's largest constituent holdings, by weight,
        descending. Empty for a plain equity, or for a fund whose
        holdings aren't individual companies (e.g. a derivative-based
        leveraged fund)."""
