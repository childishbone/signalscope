"""The provider-agnostic interface the rest of the app depends on.

Nothing outside market_data/ should import yfinance (or any other provider
library) directly. Swapping or adding a provider means writing a new class
here, not touching the callers.
"""

from abc import ABC, abstractmethod

from signalscope.market_data.types import Bar, SecurityMatch


class MarketDataProvider(ABC):
    @abstractmethod
    def search_securities(self, query: str, limit: int = 8) -> list[SecurityMatch]:
        """Search for securities, restricted to markets this app supports."""

    @abstractmethod
    def get_historical_bars(self, provider_symbol: str, period: str = "2y") -> list[Bar]:
        """Daily OHLCV bars, oldest first. Incomplete bars are excluded."""
