"""Tests for the Overall signal (signalscope.signals.overall)."""

from signalscope.signals.overall import compute_overall
from signalscope.signals.types import IndicatorResult, SignalState


def _result(state: SignalState) -> IndicatorResult:
    return IndicatorResult(state=state, score=0, reasons=[], values={})


def test_all_three_bullish_is_bullish() -> None:
    result = compute_overall(
        dma=_result(SignalState.BULLISH),
        rsi=_result(SignalState.BULLISH),
        ichimoku=_result(SignalState.BULLISH),
    )
    assert result.state is SignalState.BULLISH
    assert result.score == 2.0


def test_all_three_bearish_is_bearish() -> None:
    result = compute_overall(
        dma=_result(SignalState.BEARISH),
        rsi=_result(SignalState.BEARISH),
        ichimoku=_result(SignalState.BEARISH),
    )
    assert result.state is SignalState.BEARISH
    assert result.score == -2.0


def test_all_three_neutral_is_neutral() -> None:
    result = compute_overall(
        dma=_result(SignalState.NEUTRAL),
        rsi=_result(SignalState.NEUTRAL),
        ichimoku=_result(SignalState.NEUTRAL),
    )
    assert result.state is SignalState.NEUTRAL
    assert result.score == 0.0


def test_two_bullish_and_one_neutral_is_bullish() -> None:
    result = compute_overall(
        dma=_result(SignalState.BULLISH),
        rsi=_result(SignalState.BULLISH),
        ichimoku=_result(SignalState.NEUTRAL),
    )
    assert result.state is SignalState.BULLISH


def test_one_dissenting_indicator_leaves_overall_neutral() -> None:
    """Two Bullish and one Bearish average to +0.67, short of the +1.0
    threshold, so Overall is Neutral rather than Bullish."""
    result = compute_overall(
        dma=_result(SignalState.BULLISH),
        rsi=_result(SignalState.BULLISH),
        ichimoku=_result(SignalState.BEARISH),
    )
    assert result.state is SignalState.NEUTRAL


def test_one_bullish_alone_cannot_move_a_neutral_majority() -> None:
    result = compute_overall(
        dma=_result(SignalState.BULLISH),
        rsi=_result(SignalState.NEUTRAL),
        ichimoku=_result(SignalState.NEUTRAL),
    )
    assert result.state is SignalState.NEUTRAL


def test_reasons_explain_every_indicators_contribution() -> None:
    result = compute_overall(
        dma=_result(SignalState.BULLISH),
        rsi=_result(SignalState.BEARISH),
        ichimoku=_result(SignalState.NEUTRAL),
    )
    joined = " ".join(result.reasons)
    assert "DMA" in joined
    assert "RSI" in joined
    assert "Ichimoku" in joined
    assert "Bollinger" not in joined
    assert "Weighted average score" in joined
