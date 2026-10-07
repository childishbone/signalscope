"""Tests for the CANSLIM letters C and A scorers
(signalscope.signals.canslim_earnings)."""

from datetime import date

from signalscope.market_data.types import EpsPeriod
from signalscope.signals.canslim_earnings import (
    ANNUAL_PERIODS_REQUIRED,
    score_annual_earnings_growth,
    score_current_earnings_growth,
)
from signalscope.signals.canslim_types import CanslimVerdict


def test_c_insufficient_data_when_no_quarterly_eps() -> None:
    result = score_current_earnings_growth([])
    assert result.verdict == CanslimVerdict.INSUFFICIENT_DATA


def test_c_insufficient_data_when_no_year_ago_quarter_available() -> None:
    quarterly = [EpsPeriod(period_end=date(2026, 7, 31), eps=2.68)]
    result = score_current_earnings_growth(quarterly)
    assert result.verdict == CanslimVerdict.INSUFFICIENT_DATA


def test_c_passes_on_strong_yoy_growth() -> None:
    quarterly = [
        EpsPeriod(period_end=date(2025, 7, 31), eps=0.85),
        EpsPeriod(period_end=date(2026, 7, 31), eps=2.68),
    ]
    result = score_current_earnings_growth(quarterly)
    assert result.verdict == CanslimVerdict.PASS
    assert result.values["yoy_growth_pct"] > 25.0


def test_c_fails_on_weak_yoy_growth() -> None:
    quarterly = [
        EpsPeriod(period_end=date(2025, 7, 31), eps=2.00),
        EpsPeriod(period_end=date(2026, 7, 31), eps=2.05),
    ]
    result = score_current_earnings_growth(quarterly)
    assert result.verdict == CanslimVerdict.FAIL


def test_c_passes_on_turnaround_from_loss_to_profit() -> None:
    quarterly = [
        EpsPeriod(period_end=date(2025, 7, 31), eps=-0.50),
        EpsPeriod(period_end=date(2026, 7, 31), eps=0.30),
    ]
    result = score_current_earnings_growth(quarterly)
    assert result.verdict == CanslimVerdict.PASS
    assert "yoy_growth_pct" not in result.values


def test_c_fails_when_still_unprofitable() -> None:
    quarterly = [
        EpsPeriod(period_end=date(2025, 7, 31), eps=-0.50),
        EpsPeriod(period_end=date(2026, 7, 31), eps=-0.20),
    ]
    result = score_current_earnings_growth(quarterly)
    assert result.verdict == CanslimVerdict.FAIL


def test_a_insufficient_data_when_too_few_years() -> None:
    annual = [EpsPeriod(period_end=date(2025, 3, 31), eps=1.0)] * (ANNUAL_PERIODS_REQUIRED - 1)
    result = score_annual_earnings_growth(annual)
    assert result.verdict == CanslimVerdict.INSUFFICIENT_DATA


def test_a_passes_on_consistent_strong_growth() -> None:
    annual = [
        EpsPeriod(period_end=date(2023, 3, 31), eps=1.00),
        EpsPeriod(period_end=date(2024, 3, 31), eps=1.30),
        EpsPeriod(period_end=date(2025, 3, 31), eps=1.70),
    ]
    result = score_annual_earnings_growth(annual)
    assert result.verdict == CanslimVerdict.PASS


def test_a_fails_on_weak_average_growth() -> None:
    annual = [
        EpsPeriod(period_end=date(2023, 3, 31), eps=1.00),
        EpsPeriod(period_end=date(2024, 3, 31), eps=1.02),
        EpsPeriod(period_end=date(2025, 3, 31), eps=1.04),
    ]
    result = score_annual_earnings_growth(annual)
    assert result.verdict == CanslimVerdict.FAIL


def test_a_fails_on_one_severe_down_year_despite_good_average() -> None:
    annual = [
        EpsPeriod(period_end=date(2023, 3, 31), eps=1.00),
        EpsPeriod(period_end=date(2024, 3, 31), eps=2.00),  # +100%
        EpsPeriod(period_end=date(2025, 3, 31), eps=1.00),  # -50%, severe decline
    ]
    result = score_annual_earnings_growth(annual)
    assert result.verdict == CanslimVerdict.FAIL


def test_a_insufficient_data_when_prior_year_eps_never_positive() -> None:
    annual = [
        EpsPeriod(period_end=date(2023, 3, 31), eps=-1.0),
        EpsPeriod(period_end=date(2024, 3, 31), eps=-0.5),
        EpsPeriod(period_end=date(2025, 3, 31), eps=-0.2),
    ]
    result = score_annual_earnings_growth(annual)
    assert result.verdict == CanslimVerdict.INSUFFICIENT_DATA
