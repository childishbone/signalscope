"""52-week-high proximity: a risk gauge, not a buy/sell signal.

Classifies a security by how close its latest close is to its highest close
of the past year. In a five-year backtest (and again on a separate set of
stocks it had never seen), stocks sitting near their 52-week high suffered
smaller dips over the following month than stocks far below it. Direction
was not predictable: stocks far below their high sometimes bounced hard and
sometimes kept falling, so this should be read as "how risky has this been",
never as "buy" or "sell".

Rule:
  ratio = latest close / highest close of the last HIGH_WINDOW_DAYS

  ratio >= NEAR_HIGH_RATIO -> Bullish  (near the high: lower recent risk)
  ratio <= FAR_BELOW_RATIO -> Bearish  (far below the high: higher risk)
  otherwise                -> Neutral

Score is the ratio in 10% steps, from -4 (far below) to +2 (at the high).
"""

from __future__ import annotations

from signalscope.signals.types import IndicatorResult, SignalState

HIGH_WINDOW_DAYS = 252
NEAR_HIGH_RATIO = 0.95
FAR_BELOW_RATIO = 0.70

MINIMUM_CLOSES_REQUIRED = HIGH_WINDOW_DAYS


def score_high52(closes: list[float]) -> IndicatorResult:
    """Score proximity to the 52-week high from closes, oldest first."""
    if len(closes) < MINIMUM_CLOSES_REQUIRED:
        raise ValueError(
            f"score_high52 needs at least {MINIMUM_CLOSES_REQUIRED} closes, got {len(closes)}"
        )

    ratio = closes[-1] / max(closes[-HIGH_WINDOW_DAYS:])
    score = max(-4, min(2, int(ratio * 10) - 8))

    if ratio >= NEAR_HIGH_RATIO:
        state = SignalState.BULLISH
        reason = f"Price is {ratio * 100:.0f}% of its 52-week high: near the high (lower risk)"
    elif ratio <= FAR_BELOW_RATIO:
        state = SignalState.BEARISH
        reason = f"Price is {ratio * 100:.0f}% of its 52-week high: far below it (higher risk)"
    else:
        state = SignalState.NEUTRAL
        reason = f"Price is {ratio * 100:.0f}% of its 52-week high"

    return IndicatorResult(
        state=state,
        score=score,
        reasons=[reason],
        values={"pct_of_52w_high": round(ratio * 100, 2)},
    )
