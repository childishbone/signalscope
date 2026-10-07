"""Tests for the CANSLIM letter M scorer
(signalscope.signals.canslim_market_direction)."""

from signalscope.signals.canslim_market_direction import score_market_direction
from signalscope.signals.canslim_types import CanslimVerdict
from signalscope.signals.dma import MINIMUM_CLOSES_REQUIRED


def test_insufficient_data_when_too_few_closes() -> None:
    closes = [100.0] * (MINIMUM_CLOSES_REQUIRED - 1)
    result = score_market_direction(closes, "^GSPC")
    assert result.verdict == CanslimVerdict.INSUFFICIENT_DATA


def test_passes_when_index_is_in_an_uptrend() -> None:
    closes = [100.0 + i * 0.5 for i in range(MINIMUM_CLOSES_REQUIRED + 10)]
    result = score_market_direction(closes, "^GSPC")
    assert result.verdict == CanslimVerdict.PASS


def test_fails_when_index_is_in_a_confirmed_downtrend() -> None:
    closes = [300.0 - i * 0.5 for i in range(MINIMUM_CLOSES_REQUIRED + 10)]
    result = score_market_direction(closes, "^GSPC")
    assert result.verdict == CanslimVerdict.FAIL
