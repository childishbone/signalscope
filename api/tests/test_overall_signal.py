"""Tests for the Overall signal (signalscope.signals.overall)."""

from signalscope.signals.overall import compute_overall
from signalscope.signals.types import IndicatorResult, SignalState


def _result(state: SignalState) -> IndicatorResult:
    return IndicatorResult(state=state, score=0, reasons=[], values={})


def test_all_four_bullish_is_bullish() -> None:
    result = compute_overall(
        dma=_result(SignalState.BULLISH),
        rsi=_result(SignalState.BULLISH),
        ichimoku=_result(SignalState.BULLISH),
        elliott=_result(SignalState.BULLISH),
    )
    assert result.state is SignalState.BULLISH
    assert result.score == 2.0


def test_all_four_bearish_is_bearish() -> None:
    result = compute_overall(
        dma=_result(SignalState.BEARISH),
        rsi=_result(SignalState.BEARISH),
        ichimoku=_result(SignalState.BEARISH),
        elliott=_result(SignalState.BEARISH),
    )
    assert result.state is SignalState.BEARISH
    assert result.score == -2.0


def test_all_four_neutral_is_neutral() -> None:
    result = compute_overall(
        dma=_result(SignalState.NEUTRAL),
        rsi=_result(SignalState.NEUTRAL),
        ichimoku=_result(SignalState.NEUTRAL),
        elliott=_result(SignalState.NEUTRAL),
    )
    assert result.state is SignalState.NEUTRAL
    assert result.score == 0.0


def test_lone_dissenting_elliott_does_not_flip_a_strong_majority() -> None:
    """Three Bullish indicators plus a Bearish Elliott Wave should stay
    Bullish -- Elliott's halved weight means it can nudge, not override."""
    result = compute_overall(
        dma=_result(SignalState.BULLISH),
        rsi=_result(SignalState.BULLISH),
        ichimoku=_result(SignalState.BULLISH),
        elliott=_result(SignalState.BEARISH),
    )
    assert result.state is SignalState.BULLISH


def test_elliott_alone_cannot_move_a_neutral_majority() -> None:
    """If DMA, RSI, and Ichimoku are all Neutral, Elliott Wave's halved
    weight alone is not enough to push Overall into Bullish or Bearish."""
    result = compute_overall(
        dma=_result(SignalState.NEUTRAL),
        rsi=_result(SignalState.NEUTRAL),
        ichimoku=_result(SignalState.NEUTRAL),
        elliott=_result(SignalState.BULLISH),
    )
    assert result.state is SignalState.NEUTRAL


def test_evenly_split_indicators_is_neutral() -> None:
    result = compute_overall(
        dma=_result(SignalState.BULLISH),
        rsi=_result(SignalState.BULLISH),
        ichimoku=_result(SignalState.BEARISH),
        elliott=_result(SignalState.BEARISH),
    )
    assert result.state is SignalState.NEUTRAL


def test_reasons_explain_every_indicators_contribution() -> None:
    result = compute_overall(
        dma=_result(SignalState.BULLISH),
        rsi=_result(SignalState.BEARISH),
        ichimoku=_result(SignalState.NEUTRAL),
        elliott=_result(SignalState.BULLISH),
    )
    joined = " ".join(result.reasons)
    assert "DMA" in joined
    assert "RSI" in joined
    assert "Ichimoku" in joined
    assert "Elliott Wave" in joined
    assert "Weighted average score" in joined
