"""Dual/Triple Moving Average (DMA) indicator.

Classifies a security as Bullish, Neutral, or Bearish based on four
deterministic, configurable rules evaluated against the 20/50/200-day
simple moving averages (SMAs) of its closing price. Every rule casts a
whole-number vote; the votes are summed into a score, and the score is
mapped to a state. Nothing here is a prediction -- it is a documented,
reproducible summary of where the price sits relative to its own recent
history.

Scoring rules (each contributes -1, 0, or +1 to the score):
  1. Price vs 200-day MA        -- long-term trend filter
  2. MA stack order (20/50/200) -- are the averages aligned bullishly,
                                    bearishly, or mixed
  3. 50-day MA slope             -- is the medium-term average rising or
                                     falling vs SLOPE_LOOKBACK_DAYS ago
  4. Recent golden/death cross   -- did the 20-day MA cross the 50-day MA
                                     within CROSSOVER_LOOKBACK_DAYS

Final score >= BULLISH_THRESHOLD -> Bullish
Final score <= BEARISH_THRESHOLD -> Bearish
otherwise                        -> Neutral

All thresholds and lookback windows are named constants below, so the
scoring behaviour can be tuned later without touching the logic itself.
"""

from __future__ import annotations

from signalscope.signals.types import IndicatorResult, SignalState

SHORT_WINDOW = 20
MEDIUM_WINDOW = 50
LONG_WINDOW = 200

SLOPE_LOOKBACK_DAYS = 10
CROSSOVER_LOOKBACK_DAYS = 10

BULLISH_THRESHOLD = 2
BEARISH_THRESHOLD = -2

MINIMUM_CLOSES_REQUIRED = LONG_WINDOW + SLOPE_LOOKBACK_DAYS


def _sma(values: list[float], window: int, end: int) -> float:
    """Simple moving average of `values[end - window : end]`."""
    segment = values[end - window : end]
    return sum(segment) / window


def _recent_cross(closes: list[float]) -> str | None:
    """Detect a 20/50-day MA crossover within CROSSOVER_LOOKBACK_DAYS.

    Returns "golden" if the 20-day MA crossed from at-or-below to above
    the 50-day MA at any point in the window, "death" for the opposite,
    or None if there was no crossover. If both happen inside the window
    (rare, choppy markets), the most recent one wins.
    """
    n = len(closes)
    diffs: list[float] = []
    for end in range(n - CROSSOVER_LOOKBACK_DAYS, n + 1):
        sma20 = _sma(closes, SHORT_WINDOW, end)
        sma50 = _sma(closes, MEDIUM_WINDOW, end)
        diffs.append(sma20 - sma50)

    last_cross: str | None = None
    for prev, curr in zip(diffs, diffs[1:], strict=False):
        if prev <= 0 < curr:
            last_cross = "golden"
        elif prev >= 0 > curr:
            last_cross = "death"
    return last_cross


def score_dma(closes: list[float]) -> IndicatorResult:
    """Score the DMA indicator from a list of closing prices, oldest first.

    Requires at least MINIMUM_CLOSES_REQUIRED closes so the 200-day MA and
    its slope can both be computed.
    """
    if len(closes) < MINIMUM_CLOSES_REQUIRED:
        raise ValueError(
            f"score_dma needs at least {MINIMUM_CLOSES_REQUIRED} closes, got {len(closes)}"
        )

    n = len(closes)
    price = closes[-1]

    sma20 = _sma(closes, SHORT_WINDOW, n)
    sma50 = _sma(closes, MEDIUM_WINDOW, n)
    sma200 = _sma(closes, LONG_WINDOW, n)
    sma50_prev = _sma(closes, MEDIUM_WINDOW, n - SLOPE_LOOKBACK_DAYS)

    score = 0
    reasons: list[str] = []

    # 1. Price vs 200-day MA
    if price > sma200:
        score += 1
        reasons.append("Price is above the 200-day MA (+1)")
    else:
        score -= 1
        reasons.append("Price is below the 200-day MA (-1)")

    # 2. MA stack order
    if sma20 > sma50 > sma200:
        score += 1
        reasons.append("MAs are stacked bullishly: 20-day > 50-day > 200-day (+1)")
    elif sma20 < sma50 < sma200:
        score -= 1
        reasons.append("MAs are stacked bearishly: 20-day < 50-day < 200-day (-1)")
    else:
        reasons.append("MA stack order is mixed, no clear alignment (0)")

    # 3. 50-day MA slope
    if sma50 > sma50_prev:
        score += 1
        reasons.append(f"50-day MA is rising vs {SLOPE_LOOKBACK_DAYS} trading days ago (+1)")
    elif sma50 < sma50_prev:
        score -= 1
        reasons.append(f"50-day MA is falling vs {SLOPE_LOOKBACK_DAYS} trading days ago (-1)")
    else:
        reasons.append("50-day MA is flat (0)")

    # 4. Recent golden/death cross within the lookback window
    cross = _recent_cross(closes)
    if cross == "golden":
        score += 1
        reasons.append(
            "Golden cross: 20-day MA crossed above the 50-day MA within the "
            f"last {CROSSOVER_LOOKBACK_DAYS} trading days (+1)"
        )
    elif cross == "death":
        score -= 1
        reasons.append(
            "Death cross: 20-day MA crossed below the 50-day MA within the "
            f"last {CROSSOVER_LOOKBACK_DAYS} trading days (-1)"
        )

    if score >= BULLISH_THRESHOLD:
        state = SignalState.BULLISH
    elif score <= BEARISH_THRESHOLD:
        state = SignalState.BEARISH
    else:
        state = SignalState.NEUTRAL

    return IndicatorResult(
        state=state,
        score=score,
        reasons=reasons,
        values={
            "price": round(price, 4),
            "sma20": round(sma20, 4),
            "sma50": round(sma50, 4),
            "sma200": round(sma200, 4),
        },
    )
