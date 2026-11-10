"""MACD (Moving Average Convergence Divergence) indicator.

Classifies a security as Bullish, Neutral, or Bearish based on four
deterministic, configurable rules evaluated against MACD(12, 26, 9) of its
closing price. Every rule casts a whole-number vote; the votes are summed
into a score, and the score is mapped to a state.

MACD line   = 12-day EMA minus 26-day EMA of the close
Signal line = 9-day EMA of the MACD line
Histogram   = MACD line minus signal line

Scoring rules (each contributes -1, 0, or +1 to the score):
  1. MACD line vs signal line   -- momentum is accelerating up or down
  2. MACD line vs zero          -- the fast average is above or below the
                                    slow one (the underlying trend)
  3. Histogram slope            -- is the histogram rising or falling vs
                                    SLOPE_LOOKBACK_DAYS ago
  4. Recent signal-line cross   -- did the histogram cross zero (MACD and
                                    signal lines crossing) within
                                    CROSSOVER_LOOKBACK_DAYS

Final score >= BULLISH_THRESHOLD -> Bullish
Final score <= BEARISH_THRESHOLD -> Bearish
otherwise                        -> Neutral

Worth noting: MACD measures how momentum is changing, not just the trend's
direction. A perfectly steady climb or decline (constant slope) makes the
MACD line settle onto its signal line, so it scores near Neutral; Bullish or
Bearish needs momentum to be building or fading.
"""

from __future__ import annotations

from signalscope.signals.types import IndicatorResult, SignalState

FAST_PERIOD = 12
SLOW_PERIOD = 26
SIGNAL_PERIOD = 9

SLOPE_LOOKBACK_DAYS = 10
CROSSOVER_LOOKBACK_DAYS = 10

BULLISH_THRESHOLD = 2
BEARISH_THRESHOLD = -2

# Differences smaller than this fraction of the price are floating-point
# noise (a perfectly steady trend makes MACD and its signal line converge),
# so they count as "level" rather than casting a vote.
_TOLERANCE_FRACTION = 1e-9

# The signal line first exists after SLOW_PERIOD + SIGNAL_PERIOD - 1 closes.
# A further SLOW_PERIOD closes lets the moving averages settle after being
# seeded, plus whichever lookback window (slope or crossover) is longer.
_LONGEST_LOOKBACK = max(SLOPE_LOOKBACK_DAYS, CROSSOVER_LOOKBACK_DAYS)
MINIMUM_CLOSES_REQUIRED = (SLOW_PERIOD + SIGNAL_PERIOD - 1) + SLOW_PERIOD + _LONGEST_LOOKBACK


def _ema(values: list[float | None], period: int) -> list[float | None]:
    """Exponential moving average. Starts at the first run of `period`
    defined values (seeded with their simple average); None before that."""
    result: list[float | None] = [None] * len(values)
    first = next((i for i, v in enumerate(values) if v is not None), None)
    if first is None or len(values) < first + period:
        return result

    seed_window = values[first : first + period]
    if any(v is None for v in seed_window):
        return result
    alpha = 2.0 / (period + 1)
    ema = sum(v for v in seed_window if v is not None) / period
    result[first + period - 1] = ema
    for i in range(first + period, len(values)):
        value = values[i]
        assert value is not None
        ema = alpha * value + (1.0 - alpha) * ema
        result[i] = ema
    return result


def _macd_series(
    closes: list[float],
) -> tuple[list[float | None], list[float | None], list[float | None]]:
    """(macd line, signal line, histogram), one value per close."""
    as_optional: list[float | None] = list(closes)
    fast = _ema(as_optional, FAST_PERIOD)
    slow = _ema(as_optional, SLOW_PERIOD)
    macd: list[float | None] = [
        f - s if f is not None and s is not None else None for f, s in zip(fast, slow, strict=True)
    ]
    signal = _ema(macd, SIGNAL_PERIOD)
    histogram: list[float | None] = [
        m - s if m is not None and s is not None else None
        for m, s in zip(macd, signal, strict=True)
    ]
    return macd, signal, histogram


def score_macd(closes: list[float]) -> IndicatorResult:
    """Score the MACD indicator from a list of closing prices, oldest first.

    Requires at least MINIMUM_CLOSES_REQUIRED closes.
    """
    if len(closes) < MINIMUM_CLOSES_REQUIRED:
        raise ValueError(
            f"score_macd needs at least {MINIMUM_CLOSES_REQUIRED} closes, got {len(closes)}"
        )

    macd_series, signal_series, histogram_series = _macd_series(closes)
    macd = macd_series[-1]
    signal = signal_series[-1]
    histogram = histogram_series[-1]
    prior_histogram = histogram_series[-1 - SLOPE_LOOKBACK_DAYS]
    assert macd is not None
    assert signal is not None
    assert histogram is not None
    assert prior_histogram is not None

    tolerance = _TOLERANCE_FRACTION * abs(closes[-1])
    score = 0
    reasons: list[str] = []

    # 1. MACD line vs signal line
    if macd - signal > tolerance:
        score += 1
        reasons.append("MACD line is above its signal line (+1)")
    elif signal - macd > tolerance:
        score -= 1
        reasons.append("MACD line is below its signal line (-1)")
    else:
        reasons.append("MACD line is level with its signal line (0)")

    # 2. MACD line vs zero
    if macd > tolerance:
        score += 1
        reasons.append("MACD line is above zero: the 12-day average is above the 26-day (+1)")
    elif macd < -tolerance:
        score -= 1
        reasons.append("MACD line is below zero: the 12-day average is below the 26-day (-1)")
    else:
        reasons.append("MACD line is at zero (0)")

    # 3. Histogram slope
    if histogram - prior_histogram > tolerance:
        score += 1
        reasons.append(f"MACD histogram is rising vs {SLOPE_LOOKBACK_DAYS} trading days ago (+1)")
    elif prior_histogram - histogram > tolerance:
        score -= 1
        reasons.append(f"MACD histogram is falling vs {SLOPE_LOOKBACK_DAYS} trading days ago (-1)")
    else:
        reasons.append("MACD histogram is flat (0)")

    # 4. Recent signal-line cross within the lookback window
    window = [v for v in histogram_series[-(CROSSOVER_LOOKBACK_DAYS + 1) :] if v is not None]
    crossed_up = any(a <= tolerance < b for a, b in zip(window, window[1:], strict=False))
    crossed_down = any(a >= -tolerance > b for a, b in zip(window, window[1:], strict=False))
    if crossed_up:
        score += 1
        reasons.append(
            f"MACD crossed above its signal line within the last "
            f"{CROSSOVER_LOOKBACK_DAYS} trading days (+1)"
        )
    elif crossed_down:
        score -= 1
        reasons.append(
            f"MACD crossed below its signal line within the last "
            f"{CROSSOVER_LOOKBACK_DAYS} trading days (-1)"
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
            "macd": round(macd, 4),
            "signal": round(signal, 4),
            "histogram": round(histogram, 4),
        },
    )
