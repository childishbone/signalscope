"""Yahoo Finance provider, via the unofficial `yfinance` library.

Known limitations (see Phase 0 spike and README "Limitations" section):
- Unofficial API; not exchange-licensed; can break if Yahoo changes its site.
- Occasionally rate-limits an IP; retries are not handled here (see Phase 4C).
- The most recent daily bar can arrive with a missing close for a day or
  more after the session ends (observed on some ETFs); such bars are
  dropped by _bars_from_dataframe rather than passed on as-is.
- Earnings and fund-holdings data is noticeably thinner for non-US
  tickers, and some leveraged/derivative-based funds report a single
  "holding" that is itself another fund rather than a real company.
"""

from datetime import date
from decimal import Decimal
from typing import Any

import pandas as pd
import yfinance as yf

from signalscope.market_data.base import MarketDataProvider
from signalscope.market_data.exchanges import (
    get_exchange_info,
    is_supported_exchange,
    to_native_symbol,
)
from signalscope.market_data.types import (
    Bar,
    EarningsHistory,
    EpsPeriod,
    FundHolding,
    SecurityMatch,
)

_SUPPORTED_QUOTE_TYPES = {"EQUITY", "ETF"}
_EPS_ROW_CANDIDATES = ("Diluted EPS", "Basic EPS")


def _to_decimal(value: float) -> Decimal:
    # Route through str() to avoid carrying binary-float noise into Decimal.
    return Decimal(str(round(float(value), 6)))


def _match_from_quote(quote: dict[str, Any]) -> SecurityMatch | None:
    yahoo_code = quote.get("exchange")
    quote_type = quote.get("quoteType")
    provider_symbol = quote.get("symbol")
    name = quote.get("shortname") or quote.get("longname")

    if not (yahoo_code and provider_symbol and name):
        return None
    if quote_type not in _SUPPORTED_QUOTE_TYPES:
        return None
    info = get_exchange_info(yahoo_code)
    if info is None:
        return None

    return SecurityMatch(
        symbol=to_native_symbol(provider_symbol, yahoo_code),
        provider_symbol=provider_symbol,
        name=name,
        exchange_code=info.exchange_code,
        exchange_name=info.exchange_name,
        country=info.country,
        currency=info.currency,
        asset_type="etf" if quote_type == "ETF" else "equity",
    )


def _extract_trade_date(index_value: object) -> date:
    """pandas' DatetimeIndex entries behave like datetime but aren't typed as one."""
    if isinstance(index_value, pd.Timestamp):
        return index_value.date()
    if isinstance(index_value, date):
        return index_value
    raise TypeError(f"Unexpected index value from yfinance: {index_value!r}")


def _bars_from_dataframe(df: pd.DataFrame) -> list[Bar]:
    ohlc = ["Open", "High", "Low", "Close"]
    complete = df.dropna(subset=ohlc)  # drops the incomplete-latest-bar case from Phase 0

    bars: list[Bar] = []
    for trade_date, row in complete.iterrows():
        adj_close = row.get("Adj Close")
        bars.append(
            Bar(
                trade_date=_extract_trade_date(trade_date),
                open=_to_decimal(row["Open"]),
                high=_to_decimal(row["High"]),
                low=_to_decimal(row["Low"]),
                close=_to_decimal(row["Close"]),
                adj_close=None if pd.isna(adj_close) else _to_decimal(adj_close),
                volume=int(row["Volume"]),
            )
        )
    return bars


def _eps_periods_from_dataframe(df: pd.DataFrame | None) -> list[EpsPeriod]:
    """Pull whichever EPS row is present (preferring Diluted EPS), oldest
    first, skipping periods where the figure wasn't reported at all."""
    if df is None or df.empty:
        return []

    eps_row_name = next((name for name in _EPS_ROW_CANDIDATES if name in df.index), None)
    if eps_row_name is None:
        return []

    periods: list[EpsPeriod] = []
    for period_end, value in df.loc[eps_row_name].items():
        if pd.isna(value):
            continue
        periods.append(EpsPeriod(period_end=_extract_trade_date(period_end), eps=float(value)))

    periods.sort(key=lambda period: period.period_end)  # yfinance's columns are newest-first
    return periods


def _holdings_from_dataframe(df: pd.DataFrame | None, limit: int) -> list[FundHolding]:
    if df is None or df.empty:
        return []

    holdings: list[FundHolding] = []
    for symbol, row in df.iterrows():
        holdings.append(
            FundHolding(
                symbol=str(symbol),
                name=str(row.get("Name", "")),
                weight_pct=round(float(row.get("Holding Percent", 0.0)) * 100, 4),
            )
        )
        if len(holdings) >= limit:
            break
    return holdings


class YahooProvider(MarketDataProvider):
    def search_securities(self, query: str, limit: int = 8) -> list[SecurityMatch]:
        quotes = yf.Search(query, max_results=max(limit, 10)).quotes
        matches: list[SecurityMatch] = []
        seen: set[str] = set()

        for quote in quotes:
            yahoo_code = quote.get("exchange", "")
            if not is_supported_exchange(yahoo_code):
                continue
            match = _match_from_quote(quote)
            if match is None or match.provider_symbol in seen:
                continue
            seen.add(match.provider_symbol)
            matches.append(match)
            if len(matches) >= limit:
                break

        return matches

    def get_historical_bars(self, provider_symbol: str, period: str = "2y") -> list[Bar]:
        df = yf.Ticker(provider_symbol).history(period=period, interval="1d", auto_adjust=False)
        if df.empty:
            return []
        return _bars_from_dataframe(df)

    def get_earnings_history(self, provider_symbol: str) -> EarningsHistory:
        ticker = yf.Ticker(provider_symbol)
        quarterly = _eps_periods_from_dataframe(ticker.quarterly_income_stmt)
        annual = _eps_periods_from_dataframe(ticker.income_stmt)
        return EarningsHistory(quarterly_eps=quarterly, annual_eps=annual)

    def get_top_holdings(self, provider_symbol: str, limit: int = 10) -> list[FundHolding]:
        try:
            top_holdings = yf.Ticker(provider_symbol).get_funds_data().top_holdings
        except Exception:
            # Not a fund, or yfinance has no holdings data for it -- both are
            # normal, expected outcomes here, not errors worth surfacing.
            return []
        return _holdings_from_dataframe(top_holdings, limit)
