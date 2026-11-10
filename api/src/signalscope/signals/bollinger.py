"""Bollinger Bands indicator.

Classifies a security as Bullish, Neutral, or Bearish from where its close
sits inside Bollinger Bands(20, 2): a 20-day average of the close with
bands two standard deviations above and below it.

This is a deliberately CONTRARIAN (mean-reversion) reading: a close
stretched below the lower band is treated as oversold (bullish), and one
stretched above the upper band as overbought (bearish). That is the
opposite of a trend-follower and is the main reason it is worth having next
to DMA and Ichimoku. In a strong, sustained trend price can "walk" along a
band for weeks, so this indicator can lean against a trend that keeps
going; the backtest script is the place to see whether that happens.

Scoring rules (whole-number votes, summed into a score):
  1. Band position (%B)  -- %B is where the close sits between the lower
                             band (0) and upper band (1). %B <= 0.2 votes
                             +1, %B >= 0.8 votes -1.
  2. Band breach         -- close outside a band is a further stretch:
                             below the lower band votes +1, above the upper
                             band votes -1.
  3. Re-entry            -- within REENTRY_LOOKBACK_DAYS the close came back
                             inside a band it had broken out of: back above
                             the lower band votes +1, back below the upper
                             band votes -1.

Final score >= BULLISH_THRESHOLD -> Bullish
Final score <= BEARISH_THRESHOLD -> Bearish
otherwise                        -> Neutral

The band "squeeze" (bandwidth in its lowest SQUEEZE_PERCENTILE of the last
SQUEEZE_LOOKBACK_DAYS) is reported in the reasons and values but does not
vote: a squeeze says a bigger move is coming, not which way.
"""

from __future__ import annotations

import statistics

from signalscope.signals.types import IndicatorResult, SignalState

BB_PERIOD = 20
BB_STDEVS = 2.0

LOWER_ZONE = 0.2
UPPER_ZONE = 0.8

REENTRY_LOOKBACK_DAYS = 5

SQUEEZE_LOOKBACK_DAYS = 120
SQUEEZE_PERCENTILE = 10.0

BULLISH_THRESHOLD = 2
BEARISH_THRESHOLD = -2

MINIMUM_CLOSES_REQUIRED = BB_PERIOD + SQUEEZE_LOOKBACK_DAYS


def _bands_at(closes: list[float], end: int) -> tuple[float, float, float]:
    """(lower, middle, upper) using the BB_PERIOD closes ending before `end`."""
    window = closes[end - BB_PERIOD : end]
    middle = statistics.fmean(window)
    spread = BB_STDEVS * statistics.pstdev(window)
    return middle - spread, middle, middle + spread


def score_bollinger(closes: list[float]) -> IndicatorResult:
    """Score Bollinger Bands from a list of closing prices, oldest first.

    Requires at least MINIMUM_CLOSES_REQUIRED closes.
    """
    if len(closes) < MINIMUM_CLOSES_REQUIRED:
        raise ValueError(
            f"score_bollinger needs at least {MINIMUM_CLOSES_REQUIRED} closes, got {len(closes)}"
        )

    n = len(closes)
    price = closes[-1]
    lower, middle, upper = _bands_at(closes, n)
    width = upper - lower
    percent_b = (price - lower) / width if width > 0 else 0.5

    score = 0
    reasons: list[str] = []

    # 1. Band position (%B)
    if percent_b <= LOWER_ZONE:
        score += 1
        reasons.append(f"Close is in the bottom of the bands (%B {percent_b:.2f}), oversold (+1)")
    elif percent_b >= UPPER_ZONE:
        score -= 1
        reasons.append(f"Close is in the top of the bands (%B {percent_b:.2f}), overbought (-1)")
    else:
        reasons.append(f"Close is mid-band (%B {percent_b:.2f}) (0)")

    # 2. Band breach
    if price < lower:
        score += 1
        reasons.append("Close is below the lower band, an oversold stretch (+1)")
    elif price > upper:
        score -= 1
        reasons.append("Close is above the upper band, an overbought stretch (-1)")

    # 3. Re-entry after a breach in the last few days
    reentered_up = False
    reentered_down = False
    for end in range(n - REENTRY_LOOKBACK_DAYS, n):
        prev_lower, _, prev_upper = _bands_at(closes, end)
        cur_lower, _, cur_upper = _bands_at(closes, end + 1)
        if closes[end - 1] < prev_lower and closes[end] >= cur_lower:
            reentered_up = True
        if closes[end - 1] > prev_upper and closes[end] <= cur_upper:
            reentered_down = True
    if reentered_up and price >= lower:
        score += 1
        reasons.append(
            f"Close moved back above the lower band within the last "
            f"{REENTRY_LOOKBACK_DAYS} trading days (+1)"
        )
    elif reentered_down and price <= upper:
        score -= 1
        reasons.append(
            f"Close moved back below the upper band within the last "
            f"{REENTRY_LOOKBACK_DAYS} trading days (-1)"
        )

    # Squeeze: informational only, not a vote.
    widths: list[float] = []
    for end in range(n - SQUEEZE_LOOKBACK_DAYS + 1, n + 1):
        low, mid, high = _bands_at(closes, end)
        widths.append((high - low) / mid if mid != 0 else 0.0)
    current_width = widths[-1]
    rank = 100.0 * sum(1 for w in widths if w <= current_width) / len(widths)
    if rank <= SQUEEZE_PERCENTILE:
        reasons.append(
            f"Squeeze: band width is in the lowest {SQUEEZE_PERCENTILE:.0f}% of the last "
            f"{SQUEEZE_LOOKBACK_DAYS} trading days; a larger move may be building (no vote)"
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
            "percent_b": round(percent_b, 4),
            "bandwidth": round(current_width, 4),
            "bandwidth_rank_pct": round(rank, 1),
        },
    )
