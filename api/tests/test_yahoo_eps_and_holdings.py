"""Tests for the EPS- and holdings-extraction helpers in
signalscope.market_data.yahoo. These operate on plain DataFrames, so they
run without any network access -- the full get_earnings_history/
get_top_holdings methods (which call yfinance directly) are exercised only
by the opt-in real-network tests in test_yahoo_provider.py."""

from datetime import date

import pandas as pd

from signalscope.market_data.yahoo import (
    _eps_periods_from_dataframe,
    _holdings_from_dataframe,
)


def test_eps_periods_prefers_diluted_eps_and_skips_nan() -> None:
    df = pd.DataFrame(
        {
            pd.Timestamp("2026-01-31"): {"Diluted EPS": 2.68, "Basic EPS": 2.75},
            pd.Timestamp("2025-10-31"): {"Diluted EPS": float("nan"), "Basic EPS": 1.80},
        }
    )
    periods = _eps_periods_from_dataframe(df)

    # The NaN diluted-EPS period is dropped entirely, not silently zeroed --
    # falling back to Basic EPS for just that one period would quietly mix
    # two different metrics together.
    assert len(periods) == 1
    assert periods[0].period_end == date(2026, 1, 31)
    assert periods[0].eps == 2.68


def test_eps_periods_falls_back_to_basic_eps_when_diluted_missing() -> None:
    df = pd.DataFrame({pd.Timestamp("2026-01-31"): {"Basic EPS": 1.55}})
    periods = _eps_periods_from_dataframe(df)
    assert len(periods) == 1
    assert periods[0].eps == 1.55


def test_eps_periods_empty_dataframe_returns_empty_list() -> None:
    assert _eps_periods_from_dataframe(pd.DataFrame()) == []


def test_eps_periods_none_returns_empty_list() -> None:
    assert _eps_periods_from_dataframe(None) == []


def test_eps_periods_sorted_oldest_first() -> None:
    df = pd.DataFrame(
        {
            pd.Timestamp("2026-01-31"): {"Diluted EPS": 2.0},
            pd.Timestamp("2025-01-31"): {"Diluted EPS": 1.0},
        }
    )
    periods = _eps_periods_from_dataframe(df)
    assert [p.period_end for p in periods] == [date(2025, 1, 31), date(2026, 1, 31)]


def test_holdings_from_dataframe_respects_limit_and_weight_conversion() -> None:
    df = pd.DataFrame(
        {"Name": ["Company A", "Company B"], "Holding Percent": [0.313220, 0.205148]},
        index=pd.Index(["AAA", "BBB"], name="Symbol"),
    )
    holdings = _holdings_from_dataframe(df, limit=1)

    assert len(holdings) == 1
    assert holdings[0].symbol == "AAA"
    assert holdings[0].name == "Company A"
    assert holdings[0].weight_pct == 31.322


def test_holdings_from_dataframe_empty_or_none_returns_empty_list() -> None:
    assert _holdings_from_dataframe(pd.DataFrame(), limit=5) == []
    assert _holdings_from_dataframe(None, limit=5) == []
