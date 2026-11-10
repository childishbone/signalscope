"""Volume confirmation indicator.

Classifies a security as Bullish, Neutral, or Bearish from whether trading
volume is backing up the price moves. Price moves on heavy volume matter
more than the same moves on thin volume, so this reads the *pressure*
behind recent price changes rather than price level itself.

Scoring rules (each contributes -1, 0, or +1 to the score):
  1. On-balance volume (OBV) vs its average -- OBV adds a day's volume when
                                  the close rises and subtracts it when the
                                  close falls; OBV above its own
                                  OBV_AVERAGE_PERIOD-day average means
                                  buying pressure is building
  2. Up-day vs down-day volume -- total volume on up days divided by total
                                  volume on down days over RATIO_WINDOW days:
                                  >= UP_DOWN_BULLISH_RATIO votes +1,
                                  <= UP_DOWN_BEARISH_RATIO votes -1
  3. Volume surge              -- today's volume is at least SURGE_MULTIPLE
                                  times the prior SURGE_WINDOW-day average,
                                  voting with the direction of today's move

Final score >= BULLISH_THRESHOLD -> Bullish
Final score <= BEARISH_THRESHOLD -> Bearish
otherwise                        -> Neutral
"""

from __future__ import annotations

from signalscope.signals.types import IndicatorResult, SignalState

OBV_AVERAGE_PERIOD = 20
RATIO_WINDOW = 20
SURGE_WINDOW = 20

UP_DOWN_BULLISH_RATIO = 1.25
UP_DOWN_BEARISH_RATIO = 0.8
SURGE_MULTIPLE = 1.5

BULLISH_THRESHOLD = 2
BEARISH_THRESHOLD = -2

# OBV needs a full average window of its own history, plus a window of
# warm-up so the first averages are not dominated by the starting point.
MINIMUM_BARS_REQUIRED = 2 * OBV_AVERAGE_PERIOD + 1


def _obv_series(closes: list[float], volumes: list[float]) -> list[float]:
    """Cumulative on-balance volume, one value per close (starting at 0)."""
    obv = [0.0]
    for i in range(1, len(closes)):
        if closes[i] > closes[i - 1]:
            obv.append(obv[-1] + volumes[i])
        elif closes[i] < closes[i - 1]:
            obv.append(obv[-1] - volumes[i])
        else:
            obv.append(obv[-1])
    return obv


def score_volume(closes: list[float], volumes: list[float]) -> IndicatorResult:
    """Score volume confirmation from closes and volumes, oldest first.

    Requires at least MINIMUM_BARS_REQUIRED bars of each, equal in length.
    """
    if len(closes) != len(volumes):
        raise ValueError("closes and volumes must be the same length")
    if len(closes) < MINIMUM_BARS_REQUIRED:
        raise ValueError(
            f"score_volume needs at least {MINIMUM_BARS_REQUIRED} bars, got {len(closes)}"
        )

    n = len(closes)
    score = 0
    reasons: list[str] = []

    # 1. OBV vs its average
    obv = _obv_series(closes, volumes)
    obv_average = sum(obv[-OBV_AVERAGE_PERIOD:]) / OBV_AVERAGE_PERIOD
    if obv[-1] > obv_average:
        score += 1
        reasons.append("On-balance volume is above its recent average: buying pressure (+1)")
    elif obv[-1] < obv_average:
        score -= 1
        reasons.append("On-balance volume is below its recent average: selling pressure (-1)")
    else:
        reasons.append("On-balance volume is level with its recent average (0)")

    # 2. Up-day vs down-day volume
    up_volume = 0.0
    down_volume = 0.0
    for i in range(n - RATIO_WINDOW, n):
        if closes[i] > closes[i - 1]:
            up_volume += volumes[i]
        elif closes[i] < closes[i - 1]:
            down_volume += volumes[i]
    if down_volume > 0:
        ratio = up_volume / down_volume
    else:
        ratio = float("inf") if up_volume > 0 else 1.0
    ratio_text = f"{ratio:.2f}x" if down_volume > 0 else "no down days"
    if ratio >= UP_DOWN_BULLISH_RATIO:
        score += 1
        reasons.append(f"Up-day volume outweighs down-day volume ({ratio_text}) (+1)")
    elif ratio <= UP_DOWN_BEARISH_RATIO:
        score -= 1
        reasons.append(f"Down-day volume outweighs up-day volume ({ratio_text}) (-1)")
    else:
        reasons.append(f"Up-day and down-day volume are balanced ({ratio_text}) (0)")

    # 3. Volume surge, in the direction of today's move
    prior = volumes[n - 1 - SURGE_WINDOW : n - 1]
    average_volume = sum(prior) / SURGE_WINDOW
    surge = volumes[-1] / average_volume if average_volume > 0 else 0.0
    if surge >= SURGE_MULTIPLE and closes[-1] > closes[-2]:
        score += 1
        reasons.append(f"Today's volume surged ({surge:.1f}x average) on a rising close (+1)")
    elif surge >= SURGE_MULTIPLE and closes[-1] < closes[-2]:
        score -= 1
        reasons.append(f"Today's volume surged ({surge:.1f}x average) on a falling close (-1)")

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
            "obv": round(obv[-1], 2),
            "up_down_volume_ratio": round(min(ratio, 99.0), 4),
            "volume_vs_average": round(surge, 4),
        },
    )
