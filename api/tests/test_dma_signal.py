"""Tests for the DMA indicator scoring logic (signalscope.signals.dma)."""

import math

import pytest

from signalscope.signals.dma import MINIMUM_CLOSES_REQUIRED, score_dma
from signalscope.signals.types import SignalState


def _uptrend(n: int = 260) -> list[float]:
    return [100 + 60 * i / (n - 1) for i in range(n)]


def _downtrend(n: int = 260) -> list[float]:
    return [160 - 60 * i / (n - 1) for i in range(n)]


def _sideways(n: int = 260) -> list[float]:
    return [130 + 2 * math.sin(8 * math.pi * i / (n - 1)) for i in range(n)]


def _golden_cross(n: int = 260, recovery_len: int = 8) -> list[float]:
    """A decline that bottoms out and then recovers sharply enough that the
    20-day MA crosses back above the 50-day MA within the last 10 days."""
    decline_len = n - recovery_len
    decline = [120 - 20 * i / (decline_len - 1) for i in range(decline_len)]
    recovery = [100 + 40 * i / (recovery_len - 1) for i in range(recovery_len)]
    return decline + recovery


def _death_cross(n: int = 260, decline_len: int = 8) -> list[float]:
    """A rise that tops out and then falls sharply enough that the 20-day
    MA crosses back below the 50-day MA within the last 10 days."""
    flat_len = n - decline_len
    rise = [100 + 40 * i / (flat_len - 1) for i in range(flat_len)]
    decline = [140 - 40 * i / (decline_len - 1) for i in range(decline_len)]
    return rise + decline


def test_sustained_uptrend_is_bullish() -> None:
    result = score_dma(_uptrend())
    assert result.state is SignalState.BULLISH
    assert result.score > 0


def test_sustained_downtrend_is_bearish() -> None:
    result = score_dma(_downtrend())
    assert result.state is SignalState.BEARISH
    assert result.score < 0


def test_sideways_market_is_not_strongly_bullish() -> None:
    result = score_dma(_sideways())
    assert result.state in (SignalState.NEUTRAL, SignalState.BEARISH)


def test_golden_cross_is_detected_and_bullish() -> None:
    result = score_dma(_golden_cross())
    assert result.state is SignalState.BULLISH
    assert any("Golden cross" in reason for reason in result.reasons)


def test_death_cross_is_detected_and_bearish() -> None:
    result = score_dma(_death_cross())
    assert result.state is SignalState.BEARISH
    assert any("Death cross" in reason for reason in result.reasons)


def test_result_includes_the_computed_moving_averages() -> None:
    result = score_dma(_uptrend())
    assert set(result.values) == {"price", "sma20", "sma50", "sma200"}


def test_too_few_closes_raises_value_error() -> None:
    with pytest.raises(ValueError, match="needs at least"):
        score_dma(_uptrend(n=MINIMUM_CLOSES_REQUIRED - 1))


def test_minimum_length_input_does_not_crash() -> None:
    result = score_dma(_uptrend(n=MINIMUM_CLOSES_REQUIRED))
    assert result.state in (SignalState.BULLISH, SignalState.NEUTRAL, SignalState.BEARISH)


def test_reasons_are_never_empty() -> None:
    result = score_dma(_uptrend())
    assert len(result.reasons) >= 3
