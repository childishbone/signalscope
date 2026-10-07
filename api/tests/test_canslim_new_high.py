"""Tests for the CANSLIM letter N scorer (signalscope.signals.canslim_new_high)."""

from signalscope.signals.canslim_new_high import (
    MINIMUM_CLOSES_REQUIRED,
    NEW_HIGH_THRESHOLD_PCT,
    score_new_high,
)
from signalscope.signals.canslim_types import CanslimVerdict


def test_insufficient_data_when_too_few_closes() -> None:
    closes = [100.0] * (MINIMUM_CLOSES_REQUIRED - 1)
    result = score_new_high(closes)
    assert result.verdict == CanslimVerdict.INSUFFICIENT_DATA


def test_passes_when_price_is_near_the_high() -> None:
    # Rises steadily from 100 to 200, ending essentially at the high.
    closes = [100.0 + i for i in range(100)]
    result = score_new_high(closes)
    assert result.verdict == CanslimVerdict.PASS
    assert result.values["pct_below_high"] < 1.0


def test_fails_when_price_is_far_below_the_high() -> None:
    # Rises to a peak of ~199, then drops sharply to ~121 (well over 15% off the high).
    rising = [100.0 + i for i in range(100)]
    falling = [199.0 - i * 2 for i in range(40)]
    closes = rising + falling
    result = score_new_high(closes)
    assert result.verdict == CanslimVerdict.FAIL
    assert result.values["pct_below_high"] > NEW_HIGH_THRESHOLD_PCT
