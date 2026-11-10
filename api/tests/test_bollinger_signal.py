"""Tests for the Bollinger Bands indicator (signalscope.signals.bollinger)."""

import math

import pytest

from signalscope.signals.bollinger import MINIMUM_CLOSES_REQUIRED, score_bollinger
from signalscope.signals.types import SignalState


def _calm_oscillation(n: int = 190) -> list[float]:
    return [100 + math.sin(i * 0.5) for i in range(n)]


def _sharp_drop(steps: int = 5) -> list[float]:
    """A calm series that suddenly falls well below its lower band."""
    return _calm_oscillation() + [100 - 3 * k for k in range(1, steps + 1)]


def _sharp_spike(steps: int = 5) -> list[float]:
    return _calm_oscillation() + [100 + 3 * k for k in range(1, steps + 1)]


def _volatility_fading(n: int = 200) -> list[float]:
    """Swings that keep shrinking, so band width ends at a multi-month low."""
    return [100 + (8 * math.exp(-i / 40)) * math.sin(i * 0.9) for i in range(n)]


def test_close_far_below_lower_band_is_bullish() -> None:
    result = score_bollinger(_sharp_drop())
    assert result.state is SignalState.BULLISH
    assert any("below the lower band" in reason for reason in result.reasons)


def test_close_far_above_upper_band_is_bearish() -> None:
    result = score_bollinger(_sharp_spike())
    assert result.state is SignalState.BEARISH
    assert any("above the upper band" in reason for reason in result.reasons)


def test_flat_series_is_neutral() -> None:
    result = score_bollinger([100.0] * 200)
    assert result.state is SignalState.NEUTRAL
    assert result.values["percent_b"] == pytest.approx(0.5)


def test_mid_band_close_is_neutral() -> None:
    result = score_bollinger(_calm_oscillation())
    assert result.state is SignalState.NEUTRAL


def test_squeeze_is_reported_but_does_not_vote() -> None:
    result = score_bollinger(_volatility_fading())
    assert any("Squeeze" in reason for reason in result.reasons)
    assert result.values["bandwidth_rank_pct"] <= 10.0
    assert result.state is SignalState.NEUTRAL


def test_reports_percent_b_and_bandwidth() -> None:
    result = score_bollinger(_calm_oscillation())
    assert set(result.values) == {"percent_b", "bandwidth", "bandwidth_rank_pct"}


def test_too_few_closes_raises() -> None:
    with pytest.raises(ValueError, match="needs at least"):
        score_bollinger([100.0] * (MINIMUM_CLOSES_REQUIRED - 1))


def test_exactly_the_minimum_number_of_closes_is_accepted() -> None:
    result = score_bollinger(_calm_oscillation(MINIMUM_CLOSES_REQUIRED))
    assert result.state in set(SignalState)
