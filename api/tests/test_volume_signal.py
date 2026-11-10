"""Tests for the volume confirmation indicator (signalscope.signals.volume)."""

import pytest

from signalscope.signals.types import SignalState
from signalscope.signals.volume import MINIMUM_BARS_REQUIRED, score_volume

N = 120


def _rising_prices() -> list[float]:
    return [100 + 0.5 * i for i in range(N)]


def _falling_prices() -> list[float]:
    return [160 - 0.5 * i for i in range(N)]


def _steady_volume() -> list[float]:
    return [1000.0 + (50 if i % 2 else 0) for i in range(N)]


def test_rising_prices_on_steady_volume_is_bullish() -> None:
    result = score_volume(_rising_prices(), _steady_volume())
    assert result.state is SignalState.BULLISH


def test_falling_prices_on_steady_volume_is_bearish() -> None:
    result = score_volume(_falling_prices(), _steady_volume())
    assert result.state is SignalState.BEARISH


def test_flat_prices_are_neutral() -> None:
    result = score_volume([100.0] * N, _steady_volume())
    assert result.state is SignalState.NEUTRAL
    assert result.score == 0


def test_volume_surge_on_a_rising_close_votes_bullish() -> None:
    volumes = [1000.0] * (N - 1) + [3000.0]
    result = score_volume(_rising_prices(), volumes)
    assert any("surged" in reason and "(+1)" in reason for reason in result.reasons)


def test_volume_surge_on_a_falling_close_votes_bearish() -> None:
    volumes = [1000.0] * (N - 1) + [3000.0]
    result = score_volume(_falling_prices(), volumes)
    assert any("surged" in reason and "(-1)" in reason for reason in result.reasons)


def test_no_surge_vote_when_volume_is_ordinary() -> None:
    result = score_volume(_rising_prices(), _steady_volume())
    assert not any("surged" in reason for reason in result.reasons)


def test_zero_volume_does_not_crash() -> None:
    result = score_volume(_rising_prices(), [0.0] * N)
    assert result.state is SignalState.NEUTRAL


def test_reports_expected_values() -> None:
    result = score_volume(_rising_prices(), _steady_volume())
    assert set(result.values) == {"obv", "up_down_volume_ratio", "volume_vs_average"}


def test_mismatched_lengths_raise() -> None:
    with pytest.raises(ValueError, match="same length"):
        score_volume([100.0] * 60, [1000.0] * 59)


def test_too_few_bars_raises() -> None:
    with pytest.raises(ValueError, match="needs at least"):
        score_volume([100.0] * (MINIMUM_BARS_REQUIRED - 1), [1000.0] * (MINIMUM_BARS_REQUIRED - 1))


def test_exactly_the_minimum_number_of_bars_is_accepted() -> None:
    n = MINIMUM_BARS_REQUIRED
    result = score_volume([100 + 0.5 * i for i in range(n)], [1000.0] * n)
    assert result.state in set(SignalState)
