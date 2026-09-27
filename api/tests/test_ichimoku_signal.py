"""Tests for the Ichimoku Cloud indicator (signalscope.signals.ichimoku)."""

import math

import pytest

from signalscope.signals.ichimoku import MINIMUM_BARS_REQUIRED, score_ichimoku
from signalscope.signals.types import SignalState


def _hlc_uptrend(n: int = 150) -> tuple[list[float], list[float], list[float]]:
    closes = [100 + 0.5 * i for i in range(n)]
    highs = [c + 1.0 for c in closes]
    lows = [c - 1.0 for c in closes]
    return highs, lows, closes


def _hlc_downtrend(n: int = 150) -> tuple[list[float], list[float], list[float]]:
    closes = [200 - 0.5 * i for i in range(n)]
    highs = [c + 1.0 for c in closes]
    lows = [c - 1.0 for c in closes]
    return highs, lows, closes


def _hlc_sideways(n: int = 150) -> tuple[list[float], list[float], list[float]]:
    closes = [130 + 3 * math.sin(i * 0.3) for i in range(n)]
    highs = [c + 1.0 for c in closes]
    lows = [c - 1.0 for c in closes]
    return highs, lows, closes


def _hlc_flat(n: int) -> tuple[list[float], list[float], list[float]]:
    closes = [100.0] * n
    return closes[:], closes[:], closes[:]


def test_sustained_uptrend_is_bullish() -> None:
    highs, lows, closes = _hlc_uptrend()
    result = score_ichimoku(highs, lows, closes)
    assert result.state is SignalState.BULLISH
    assert result.score == 4


def test_sustained_downtrend_is_bearish() -> None:
    highs, lows, closes = _hlc_downtrend()
    result = score_ichimoku(highs, lows, closes)
    assert result.state is SignalState.BEARISH
    assert result.score == -4


def test_flat_market_is_neutral() -> None:
    highs, lows, closes = _hlc_flat(150)
    result = score_ichimoku(highs, lows, closes)
    assert result.state is SignalState.NEUTRAL
    assert result.score == 0


def test_result_includes_the_computed_lines() -> None:
    highs, lows, closes = _hlc_uptrend()
    result = score_ichimoku(highs, lows, closes)
    assert set(result.values) == {
        "tenkan",
        "kijun",
        "senkou_a",
        "senkou_b",
        "chikou_reference_price",
    }


def test_mismatched_list_lengths_raise_value_error() -> None:
    highs, lows, closes = _hlc_uptrend()
    with pytest.raises(ValueError, match="same length"):
        score_ichimoku(highs[:-1], lows, closes)


def test_too_few_bars_raises_value_error() -> None:
    highs, lows, closes = _hlc_uptrend(n=MINIMUM_BARS_REQUIRED - 1)
    with pytest.raises(ValueError, match="needs at least"):
        score_ichimoku(highs, lows, closes)


def test_minimum_length_input_does_not_crash() -> None:
    highs, lows, closes = _hlc_uptrend(n=MINIMUM_BARS_REQUIRED)
    result = score_ichimoku(highs, lows, closes)
    assert result.state in (SignalState.BULLISH, SignalState.NEUTRAL, SignalState.BEARISH)


def test_reasons_are_never_empty() -> None:
    highs, lows, closes = _hlc_uptrend()
    result = score_ichimoku(highs, lows, closes)
    assert len(result.reasons) == 4
