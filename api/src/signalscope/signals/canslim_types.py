"""Shared types for the CANSLIM checklist.

CANSLIM is a different shape of analysis than the existing Bullish /
Neutral / Bearish indicators: each letter is a pass/fail check against a
specific criterion, and for some securities (ETFs with no earnings,
stocks with too little price history) a criterion genuinely can't be
evaluated at all. That third state -- insufficient data -- must never be
silently folded into "fail", since that would understate the security's
real CANSLIM score rather than just reporting less about it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class CanslimVerdict(StrEnum):
    """The three states any individual CANSLIM letter can resolve to."""

    PASS = "pass"
    FAIL = "fail"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass(frozen=True)
class CanslimLetterResult:
    """The output of scoring one CANSLIM letter for one security.

    `reasons` and `values` follow the same convention as IndicatorResult
    elsewhere in this codebase, so the frontend can show the reasoning
    behind a Pass/Fail/Insufficient-data verdict the same way it already
    does for DMA/RSI/Ichimoku/Elliott.
    """

    letter: str
    verdict: CanslimVerdict
    reasons: list[str] = field(default_factory=list)
    values: dict[str, float] = field(default_factory=dict)
