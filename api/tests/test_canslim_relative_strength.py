"""Tests for the CANSLIM letter L scorer
(signalscope.signals.canslim_relative_strength)."""

from signalscope.signals.canslim_relative_strength import (
    MINIMUM_CLOSES_REQUIRED,
    score_relative_strength,
)
from signalscope.signals.canslim_types import CanslimVerdict


def test_insufficient_data_when_security_history_too_short() -> None:
    security_closes = [100.0] * (MINIMUM_CLOSES_REQUIRED - 1)
    benchmark_closes = [100.0] * 100
    result = score_relative_strength(security_closes, benchmark_closes, "^GSPC")
    assert result.verdict == CanslimVerdict.INSUFFICIENT_DATA


def test_insufficient_data_when_benchmark_history_too_short() -> None:
    security_closes = [100.0] * 100
    benchmark_closes = [100.0] * (MINIMUM_CLOSES_REQUIRED - 1)
    result = score_relative_strength(security_closes, benchmark_closes, "^GSPC")
    assert result.verdict == CanslimVerdict.INSUFFICIENT_DATA


def test_passes_when_security_outperforms_benchmark() -> None:
    security_closes = [100.0 + i for i in range(100)]
    benchmark_closes = [100.0 + i * 0.1 for i in range(100)]
    result = score_relative_strength(security_closes, benchmark_closes, "^GSPC")
    assert result.verdict == CanslimVerdict.PASS
    assert result.values["excess_return_pct"] > 0


def test_fails_when_security_underperforms_benchmark() -> None:
    security_closes = [100.0 + i * 0.1 for i in range(100)]
    benchmark_closes = [100.0 + i for i in range(100)]
    result = score_relative_strength(security_closes, benchmark_closes, "^GSPC")
    assert result.verdict == CanslimVerdict.FAIL
    assert result.values["excess_return_pct"] < 0
