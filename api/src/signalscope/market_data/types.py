"""Provider-agnostic data shapes. No provider (Yahoo, Stooq, ...) leaks past this module."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class SecurityMatch:
    """One search result, already filtered to a supported exchange."""

    symbol: str  # native ticker, e.g. "7203"
    provider_symbol: str  # this provider's ticker, e.g. "7203.T"
    name: str
    exchange_code: str  # our internal code, e.g. "XJPX"
    exchange_name: str
    country: str  # ISO 3166 alpha-2
    currency: str  # ISO 4217
    asset_type: str  # "equity" | "etf"


@dataclass(frozen=True)
class Bar:
    """One validated daily candle. Never contains a missing OHLC price."""

    trade_date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    adj_close: Decimal | None
    volume: int
