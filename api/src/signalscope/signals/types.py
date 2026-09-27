"""Shared types used by every technical-analysis indicator."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class SignalState(StrEnum):
    """The three states every indicator (and the Overall signal) is
    classified into."""

    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"


@dataclass(frozen=True)
class IndicatorResult:
    """The output of scoring one indicator for one security on one day.

    `score` is a small signed number that fed into the `state`
    classification -- kept on the result so a detail screen can show the
    reader exactly how the verdict was reached. Individual indicators use
    whole numbers; the Overall signal (which combines several indicators
    via a weighted average) uses a fraction, hence `float` rather than
    `int`.
    """

    state: SignalState
    score: float
    reasons: list[str] = field(default_factory=list)
    values: dict[str, float] = field(default_factory=dict)
