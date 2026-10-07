"""Tests for the CANSLIM letter S scorer
(signalscope.signals.canslim_supply_demand)."""

from signalscope.signals.canslim_supply_demand import (
    MINIMUM_CLOSES_REQUIRED,
    score_supply_demand,
)
from signalscope.signals.canslim_types import CanslimVerdict


def _alternating_closes_and_volumes(
    up_volume: int, down_volume: int
) -> tuple[list[float], list[int]]:
    """50 trading days alternating up/down moves, with distinct volume
    levels on up days vs down days, so the ratio is unambiguous."""
    closes = [100.0]
    for i in range(50):
        closes.append(closes[-1] + 2 if i % 2 == 0 else closes[-1] - 1)

    volumes = [1000]
    for i in range(1, len(closes)):
        volumes.append(up_volume if closes[i] > closes[i - 1] else down_volume)

    return closes, volumes


def test_insufficient_data_when_too_few_trading_days() -> None:
    closes = [100.0] * (MINIMUM_CLOSES_REQUIRED - 1)
    volumes = [1000] * (MINIMUM_CLOSES_REQUIRED - 1)
    result = score_supply_demand(closes, volumes)
    assert result.verdict == CanslimVerdict.INSUFFICIENT_DATA


def test_insufficient_data_when_too_few_up_or_down_days() -> None:
    # Flat price series: no up days and no down days at all.
    closes = [100.0] * MINIMUM_CLOSES_REQUIRED
    volumes = [1000] * MINIMUM_CLOSES_REQUIRED
    result = score_supply_demand(closes, volumes)
    assert result.verdict == CanslimVerdict.INSUFFICIENT_DATA


def test_passes_when_up_day_volume_exceeds_down_day_volume() -> None:
    closes, volumes = _alternating_closes_and_volumes(up_volume=5000, down_volume=1000)
    result = score_supply_demand(closes, volumes)
    assert result.verdict == CanslimVerdict.PASS
    assert result.values["up_down_volume_ratio"] > 1.0


def test_fails_when_down_day_volume_exceeds_up_day_volume() -> None:
    closes, volumes = _alternating_closes_and_volumes(up_volume=1000, down_volume=5000)
    result = score_supply_demand(closes, volumes)
    assert result.verdict == CanslimVerdict.FAIL
    assert result.values["up_down_volume_ratio"] < 1.0
