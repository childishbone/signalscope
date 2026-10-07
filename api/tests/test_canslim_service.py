"""Tests for the CANSLIM orchestration service (signalscope.services.canslim)."""

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from signalscope.db.models import DailyBar, Security
from signalscope.market_data.base import MarketDataProvider
from signalscope.market_data.types import (
    Bar,
    EarningsHistory,
    EpsPeriod,
    FundHolding,
    SecurityMatch,
)
from signalscope.services.canslim import compute_canslim_for_security
from signalscope.signals.canslim_types import CanslimVerdict


class _FakeProvider(MarketDataProvider):
    """A MarketDataProvider test double with no network calls -- every
    method returns canned data set up per test."""

    def __init__(
        self,
        earnings_by_symbol: dict[str, EarningsHistory] | None = None,
        top_holdings: list[FundHolding] | None = None,
    ) -> None:
        self.earnings_by_symbol = earnings_by_symbol or {}
        self.top_holdings = top_holdings or []

    def search_securities(self, query: str, limit: int = 8) -> list[SecurityMatch]:
        raise NotImplementedError

    def get_historical_bars(self, provider_symbol: str, period: str = "2y") -> list[Bar]:
        raise NotImplementedError

    def get_earnings_history(self, provider_symbol: str) -> EarningsHistory:
        return self.earnings_by_symbol.get(
            provider_symbol, EarningsHistory(quarterly_eps=[], annual_eps=[])
        )

    def get_top_holdings(self, provider_symbol: str, limit: int = 10) -> list[FundHolding]:
        return self.top_holdings[:limit]


def _insert_security(
    db_session: Session, symbol: str, country: str = "US", asset_type: str = "equity"
) -> Security:
    security = Security(
        symbol=symbol,
        exchange_code="NMS",
        exchange_name="NASDAQ",
        country=country,
        currency="USD",
        name=f"{symbol} Inc.",
        asset_type=asset_type,
        provider_symbol=symbol,
    )
    db_session.add(security)
    db_session.commit()
    return security


def _insert_rising_bars(db_session: Session, security_id: int, count: int = 300) -> None:
    start = date(2025, 1, 1)
    for i in range(count):
        price = Decimal(str(100.0 + i * 0.5))
        db_session.add(
            DailyBar(
                security_id=security_id,
                trade_date=start + timedelta(days=i),
                open=price,
                high=price,
                low=price,
                close=price,
                adj_close=price,
                volume=1000 + (i % 5) * 100,
            )
        )
    db_session.commit()


def test_equity_with_no_data_resolves_every_letter_to_insufficient(db_session: Session) -> None:
    security = _insert_security(db_session, "ZZZ")
    provider = _FakeProvider()

    result = compute_canslim_for_security(
        db_session, security, provider, benchmark_closes=[], benchmark_symbol="^GSPC"
    )

    assert result.criteria_evaluated == 0
    assert result.score_pct is None
    assert all(r.verdict == CanslimVerdict.INSUFFICIENT_DATA for r in result.letters.values())


def test_no_benchmark_configured_marks_m_and_l_insufficient(db_session: Session) -> None:
    security = _insert_security(db_session, "AAA", country="ZZ")
    _insert_rising_bars(db_session, security.id)
    provider = _FakeProvider()

    result = compute_canslim_for_security(
        db_session, security, provider, benchmark_closes=[], benchmark_symbol=None
    )

    assert result.letters["M"].verdict == CanslimVerdict.INSUFFICIENT_DATA
    assert result.letters["L"].verdict == CanslimVerdict.INSUFFICIENT_DATA


def test_equity_uses_its_own_earnings_history(db_session: Session) -> None:
    security = _insert_security(db_session, "BBB")
    _insert_rising_bars(db_session, security.id)
    provider = _FakeProvider(
        earnings_by_symbol={
            "BBB": EarningsHistory(
                quarterly_eps=[
                    EpsPeriod(period_end=date(2025, 7, 31), eps=0.50),
                    EpsPeriod(period_end=date(2026, 7, 31), eps=1.00),
                ],
                annual_eps=[
                    EpsPeriod(period_end=date(2023, 12, 31), eps=1.00),
                    EpsPeriod(period_end=date(2024, 12, 31), eps=1.50),
                    EpsPeriod(period_end=date(2025, 12, 31), eps=2.20),
                ],
            )
        }
    )
    benchmark_closes = [100.0 + i * 0.1 for i in range(300)]

    result = compute_canslim_for_security(
        db_session, security, provider, benchmark_closes=benchmark_closes, benchmark_symbol="^GSPC"
    )

    assert result.letters["C"].verdict == CanslimVerdict.PASS
    assert result.letters["A"].verdict == CanslimVerdict.PASS
    assert result.criteria_total == 6


def test_etf_with_too_few_holdings_resolves_c_and_a_to_insufficient(db_session: Session) -> None:
    security = _insert_security(db_session, "ZZTESTKORU", asset_type="etf")
    _insert_rising_bars(db_session, security.id)
    provider = _FakeProvider(
        top_holdings=[
            FundHolding(symbol="EWY", name="iShares MSCI South Korea ETF", weight_pct=18.7)
        ]
    )

    result = compute_canslim_for_security(
        db_session, security, provider, benchmark_closes=[], benchmark_symbol="^KS11"
    )

    assert result.letters["C"].verdict == CanslimVerdict.INSUFFICIENT_DATA
    assert result.letters["A"].verdict == CanslimVerdict.INSUFFICIENT_DATA
    assert result.letters["C"].constituents is None


def test_etf_with_enough_holdings_aggregates_weighted_verdicts(db_session: Session) -> None:
    security = _insert_security(db_session, "ZZTESTNK", country="JP", asset_type="etf")
    _insert_rising_bars(db_session, security.id)

    holdings = [
        FundHolding(symbol="8306.T", name="Mitsubishi UFJ", weight_pct=31.3),
        FundHolding(symbol="8316.T", name="Sumitomo Mitsui", weight_pct=20.5),
        FundHolding(symbol="8411.T", name="Mizuho", weight_pct=16.2),
        FundHolding(symbol="7182.T", name="Japan Post Bank", weight_pct=5.0),
        FundHolding(symbol="8308.T", name="Resona", weight_pct=4.2),
    ]
    growing_quarterly = [
        EpsPeriod(period_end=date(2025, 6, 30), eps=50.0),
        EpsPeriod(period_end=date(2026, 6, 30), eps=100.0),  # +100% YoY, clearly passes
    ]
    earnings_by_symbol = {
        h.symbol: EarningsHistory(quarterly_eps=growing_quarterly, annual_eps=[]) for h in holdings
    }
    provider = _FakeProvider(earnings_by_symbol=earnings_by_symbol, top_holdings=holdings)

    result = compute_canslim_for_security(
        db_session, security, provider, benchmark_closes=[], benchmark_symbol="^N225"
    )

    letter_c = result.letters["C"]
    assert letter_c.verdict == CanslimVerdict.PASS
    assert letter_c.constituents is not None
    assert len(letter_c.constituents) == 5
    assert letter_c.values["coverage_pct"] == 77.2
