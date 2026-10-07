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


@dataclass(frozen=True)
class EpsPeriod:
    """One reported diluted (or basic, if diluted wasn't available) EPS
    figure for one fiscal period, as reported by the provider -- not every
    period a security has existed for necessarily has one."""

    period_end: date
    eps: float


@dataclass(frozen=True)
class EarningsHistory:
    """A security's EPS history, oldest first in each list. Either list
    may be shorter than hoped (or empty) -- CANSLIM letters C and A treat
    that as insufficient data, not a failure."""

    quarterly_eps: list[EpsPeriod]
    annual_eps: list[EpsPeriod]


@dataclass(frozen=True)
class FundHolding:
    """One constituent of an ETF/fund's reported top holdings."""

    symbol: str
    name: str
    weight_pct: float  # e.g. 31.3 for a 31.3% weighting
