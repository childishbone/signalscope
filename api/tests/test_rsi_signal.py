"""Tests for the RSI indicator scoring logic (signalscope.signals.rsi)."""

import math

import pytest

from signalscope.signals.rsi import MINIMUM_CLOSES_REQUIRED, score_rsi
from signalscope.signals.types import SignalState


def _moderate_uptrend(n: int = 150) -> list[float]:
    """Drifts up with regular small pullbacks -- realistic momentum,
    not pinned at an extreme."""
    return [100 + 0.3 * i + 3 * math.sin(i * 0.8) for i in range(n)]


def _moderate_downtrend(n: int = 150) -> list[float]:
    return [160 - 0.3 * i + 3 * math.sin(i * 0.7) for i in range(n)]


def _flat_then_sharp_rally(n: int = 150, flat: float = 130.0, rally_len: int = 14) -> list[float]:
    """14 straight up days after a flat period -- pins RSI at its
    overbought extreme."""
    base = [flat] * (n - rally_len)
    rally = [flat + 1.2 * i for i in range(1, rally_len + 1)]
    return base + rally


def _flat_then_sharp_selloff(n: int = 150, flat: float = 130.0, drop_len: int = 14) -> list[float]:
    base = [flat] * (n - drop_len)
    selloff = [flat - 1.2 * i for i in range(1, drop_len + 1)]
    return base + selloff


def _decline_then_recover(n: int = 150, recovery_len: int = 6) -> list[float]:
    """A decline that bottoms out and recovers sharply enough that RSI
    crosses back above the midline within the last 10 days."""
    decline_len = n - recovery_len
    decline = [140 - 25 * i / (decline_len - 1) for i in range(decline_len)]
    recovery = [115 + 25 * i / (recovery_len - 1) for i in range(recovery_len)]
    return decline + recovery


def _rise_then_fall(n: int = 150, fall_len: int = 6) -> list[float]:
    """A rise that tops out and falls sharply enough that RSI crosses
    back below the midline within the last 10 days."""
    rise_len = n - fall_len
    rise = [115 + 25 * i / (rise_len - 1) for i in range(rise_len)]
    fall = [140 - 25 * i / (fall_len - 1) for i in range(fall_len)]
    return rise + fall


def test_moderate_uptrend_is_bullish() -> None:
    result = score_rsi(_moderate_uptrend())
    assert result.state is SignalState.BULLISH
    assert result.score > 0


def test_moderate_downtrend_is_bearish() -> None:
    result = score_rsi(_moderate_downtrend())
    assert result.state is SignalState.BEARISH
    assert result.score < 0


def test_sharp_rally_triggers_overbought_caution() -> None:
    result = score_rsi(_flat_then_sharp_rally())
    assert any("overbought" in reason for reason in result.reasons)


def test_sharp_selloff_triggers_oversold_flag() -> None:
    result = score_rsi(_flat_then_sharp_selloff())
    assert any("oversold" in reason for reason in result.reasons)


def test_bullish_midline_cross_is_detected() -> None:
    result = score_rsi(_decline_then_recover())
    assert any("crossed above" in reason for reason in result.reasons)
    assert result.state is SignalState.BULLISH


def test_bearish_midline_cross_is_detected() -> None:
    result = score_rsi(_rise_then_fall())
    assert any("crossed below" in reason for reason in result.reasons)
    assert result.state is SignalState.BEARISH


def test_result_includes_the_computed_rsi_value() -> None:
    result = score_rsi(_moderate_uptrend())
    assert set(result.values) == {"rsi"}
    assert 0 <= result.values["rsi"] <= 100


def test_too_few_closes_raises_value_error() -> None:
    with pytest.raises(ValueError, match="needs at least"):
        score_rsi(_moderate_uptrend(n=MINIMUM_CLOSES_REQUIRED - 1))


def test_minimum_length_input_does_not_crash() -> None:
    result = score_rsi(_moderate_uptrend(n=MINIMUM_CLOSES_REQUIRED))
    assert result.state in (SignalState.BULLISH, SignalState.NEUTRAL, SignalState.BEARISH)


def test_reasons_are_never_empty() -> None:
    result = score_rsi(_moderate_uptrend())
    assert len(result.reasons) >= 2
