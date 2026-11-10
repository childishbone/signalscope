"""Tests for the 52-week-high proximity indicator (signalscope.signals.high52)."""

import pytest

from signalscope.signals.high52 import MINIMUM_CLOSES_REQUIRED, score_high52
from signalscope.signals.types import SignalState


def _rising(n: int = 300) -> list[float]:
    return [100 + i * 0.5 for i in range(n)]


def test_close_at_the_high_is_bullish() -> None:
    result = score_high52(_rising())
    assert result.state is SignalState.BULLISH
    assert result.score == 2
    assert result.values["pct_of_52w_high"] == pytest.approx(100.0)


def test_close_far_below_the_high_is_bearish() -> None:
    closes = _rising() + [100.0] * 3
    result = score_high52(closes)
    assert result.state is SignalState.BEARISH
    assert any("higher risk" in reason for reason in result.reasons)


def test_close_part_way_below_the_high_is_neutral() -> None:
    peak = 250.0
    closes = [peak] * 260 + [peak * 0.85]
    result = score_high52(closes)
    assert result.state is SignalState.NEUTRAL


def test_highs_older_than_a_year_are_ignored() -> None:
    old_peak = [1000.0] * 5
    closes = old_peak + [100.0] * 300
    result = score_high52(closes)
    assert result.state is SignalState.BULLISH
    assert result.values["pct_of_52w_high"] == pytest.approx(100.0)


def test_too_few_closes_raises() -> None:
    with pytest.raises(ValueError):
        score_high52([100.0] * (MINIMUM_CLOSES_REQUIRED - 1))
