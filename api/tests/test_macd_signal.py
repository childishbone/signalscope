"""Tests for the MACD indicator scoring logic (signalscope.signals.macd)."""

import math

import pytest

from signalscope.signals.macd import MINIMUM_CLOSES_REQUIRED, score_macd
from signalscope.signals.types import SignalState


def _oscillating_uptrend(n: int = 200) -> list[float]:
    """Drifts up with regular pullbacks -- realistic momentum."""
    return [100 + 0.3 * i + 3 * math.sin(i * 0.8) for i in range(n)]


def _decline_then_recover(n: int = 150, recovery_len: int = 6) -> list[float]:
    """A decline that bottoms out and recovers sharply, so the MACD line
    crosses back above its signal line within the last 10 days."""
    decline_len = n - recovery_len
    decline = [140 - 25 * i / (decline_len - 1) for i in range(decline_len)]
    recovery = [115 + 25 * i / (recovery_len - 1) for i in range(recovery_len)]
    return decline + recovery


def _rise_then_fall(n: int = 150, fall_len: int = 6) -> list[float]:
    """A rise that tops out and falls sharply, so the MACD line crosses
    back below its signal line within the last 10 days."""
    rise_len = n - fall_len
    rise = [115 + 25 * i / (rise_len - 1) for i in range(rise_len)]
    fall = [140 - 25 * i / (fall_len - 1) for i in range(fall_len)]
    return rise + fall


def test_oscillating_uptrend_is_bullish() -> None:
    result = score_macd(_oscillating_uptrend())
    assert result.state is SignalState.BULLISH
    assert result.score > 0


def test_recovery_after_decline_is_bullish_with_cross() -> None:
    result = score_macd(_decline_then_recover())
    assert result.state is SignalState.BULLISH
    assert any("crossed above" in reason for reason in result.reasons)


def test_selloff_after_rise_is_bearish_with_cross() -> None:
    result = score_macd(_rise_then_fall())
    assert result.state is SignalState.BEARISH
    assert any("crossed below" in reason for reason in result.reasons)


def test_flat_series_is_neutral() -> None:
    result = score_macd([100.0] * 200)
    assert result.state is SignalState.NEUTRAL
    assert result.score == 0


def test_steady_straight_line_trend_is_not_strongly_directional() -> None:
    """A constant-slope trend has no building momentum, so MACD stays
    Neutral rather than being swept up by floating-point noise."""
    rising = score_macd([100 + 0.5 * i for i in range(200)])
    falling = score_macd([200 - 0.5 * i for i in range(200)])
    assert rising.state is SignalState.NEUTRAL
    assert falling.state is SignalState.NEUTRAL


def test_reports_macd_signal_and_histogram_values() -> None:
    result = score_macd(_oscillating_uptrend())
    assert set(result.values) == {"macd", "signal", "histogram"}
    assert result.values["histogram"] == pytest.approx(
        result.values["macd"] - result.values["signal"], abs=1e-3
    )


def test_every_rule_adds_a_reason() -> None:
    result = score_macd(_oscillating_uptrend())
    assert len(result.reasons) >= 3


def test_too_few_closes_raises() -> None:
    with pytest.raises(ValueError, match="needs at least"):
        score_macd([100.0] * (MINIMUM_CLOSES_REQUIRED - 1))


def test_exactly_the_minimum_number_of_closes_is_accepted() -> None:
    result = score_macd(_oscillating_uptrend(MINIMUM_CLOSES_REQUIRED))
    assert result.state in set(SignalState)
