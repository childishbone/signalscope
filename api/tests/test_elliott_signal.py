"""Tests for the Elliott Wave heuristic (signalscope.signals.elliott)."""

import pytest

from signalscope.signals.elliott import MINIMUM_CLOSES_REQUIRED, score_elliott_wave
from signalscope.signals.types import SignalState


def _flat(n: int = MINIMUM_CLOSES_REQUIRED) -> list[float]:
    return [100.0] * n


def _clean_5wave_up() -> list[float]:
    closes: list[float] = []
    closes += [100 + (20 / 19) * i for i in range(20)]
    closes += [120 - (8 / 11) * i for i in range(1, 12)]
    closes += [112 + (48 / 24) * i for i in range(1, 25)]
    closes += [160 - (15 / 9) * i for i in range(1, 10)]
    closes += [145 + (30 / 17) * i for i in range(1, 18)]
    return closes


def _invalid_wave2_retrace() -> list[float]:
    closes: list[float] = [100.0] * 7  # flat lead-in so total length >= minimum
    closes += [100 + (20 / 19) * i for i in range(20)]  # wave1 up: 100 -> 120
    closes += [120 - (35 / 14) * i for i in range(1, 15)]  # crashes to 85 (below wave1 start)
    closes += [85 + (30 / 19) * i for i in range(1, 20)]  # wave3 up: 85 -> 115
    return closes


def _three_swing_move() -> list[float]:
    closes: list[float] = [150.0] * 5  # flat lead-in so total length >= minimum
    closes += [150 - (30 / 19) * i for i in range(20)]
    closes += [120 + (10 / 11) * i for i in range(1, 12)]
    closes += [130 - (40 / 24) * i for i in range(1, 25)]
    return closes


def test_insufficient_swings_defaults_to_neutral() -> None:
    result = score_elliott_wave(_flat())
    assert result.state is SignalState.NEUTRAL
    assert any("Not enough distinct price swings" in r for r in result.reasons)


def test_invalid_wave2_retrace_is_flagged_low_confidence() -> None:
    result = score_elliott_wave(_invalid_wave2_retrace())
    assert result.state is SignalState.NEUTRAL
    assert any("Rule violation" in r for r in result.reasons)
    assert result.values["pattern_valid"] == 0.0


def test_wave_position_three_is_classified_in_leg_direction() -> None:
    result = score_elliott_wave(_three_swing_move())
    assert result.state is SignalState.BEARISH
    assert result.values["wave_position"] == 3.0
    # The genuine ambiguity between an impulse and a 3-wave correction
    # must be disclosed, not hidden.
    assert any("A-B-C correction" in r for r in result.reasons)


def test_wave5_completion_is_neutral_with_reversal_caution() -> None:
    result = score_elliott_wave(_clean_5wave_up())
    assert result.state is SignalState.NEUTRAL
    assert result.values["wave_position"] == 5.0
    assert any("expects a corrective A-B-C retracement" in r for r in result.reasons)


def test_disclaimer_is_always_the_first_reason() -> None:
    for closes in (_flat(), _clean_5wave_up(), _invalid_wave2_retrace(), _three_swing_move()):
        result = score_elliott_wave(closes)
        assert "not an objective fact" in result.reasons[0]


def test_too_few_closes_raises_value_error() -> None:
    with pytest.raises(ValueError, match="needs at least"):
        score_elliott_wave(_flat(n=MINIMUM_CLOSES_REQUIRED - 1))


def test_minimum_length_input_does_not_crash() -> None:
    result = score_elliott_wave(_flat(n=MINIMUM_CLOSES_REQUIRED))
    assert result.state in (SignalState.BULLISH, SignalState.NEUTRAL, SignalState.BEARISH)
