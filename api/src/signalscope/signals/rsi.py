"""Relative Strength Index (RSI) indicator.

Classifies a security as Bullish, Neutral, or Bearish based on four
deterministic, configurable rules evaluated against Wilder's RSI(14) of
its closing price. Every rule casts a whole-number vote; the votes are
summed into a score, and the score is mapped to a state.

Scoring rules (each contributes -1, 0, or +1 to the score):
  1. RSI vs the 50 midline        -- is short-term momentum up or down
  2. Overbought / oversold        -- RSI >= 70 is treated as overbought
                                      (a caution flag, not automatically
                                      bearish -- it can also mean a strong
                                      trend), RSI <= 30 as oversold
  3. RSI slope                     -- is RSI rising or falling vs
                                       SLOPE_LOOKBACK_DAYS ago
  4. Recent midline cross          -- did RSI cross the 50 midline within
                                       CROSSOVER_LOOKBACK_DAYS

Final score >= BULLISH_THRESHOLD -> Bullish
Final score <= BEARISH_THRESHOLD -> Bearish
otherwise                        -> Neutral

Worth noting honestly: the overbought/oversold rule is intentionally
contrarian. A security in a powerful, sustained rally can have RSI pinned
near 100, which cancels out the midline bonus and produces a "Neutral"
verdict rather than "Bullish" -- the scoring is flagging that momentum is
statistically extended, not that the trend has reversed. This is a
documented property of the scheme, not a bug, and is exactly why the
Overall signal (a later phase) combines several indicators rather than
trusting any single oscillator.
"""

from __future__ import annotations

from signalscope.signals.types import IndicatorResult, SignalState

RSI_PERIOD = 14

SLOPE_LOOKBACK_DAYS = 10
CROSSOVER_LOOKBACK_DAYS = 10

OVERBOUGHT = 70.0
OVERSOLD = 30.0
MIDLINE = 50.0

BULLISH_THRESHOLD = 2
BEARISH_THRESHOLD = -2

# Two periods of warm-up so Wilder's smoothing has stabilised, plus
# whichever lookback window (slope or crossover) is longer.
MINIMUM_CLOSES_REQUIRED = (2 * RSI_PERIOD) + max(SLOPE_LOOKBACK_DAYS, CROSSOVER_LOOKBACK_DAYS)


def _rsi_from_averages(avg_gain: float, avg_loss: float) -> float:
    if avg_gain == 0 and avg_loss == 0:
        return 50.0
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _rsi_series(closes: list[float]) -> list[float | None]:
    """Wilder's RSI(RSI_PERIOD), one value per close (None where undefined)."""
    n = len(closes)
    result: list[float | None] = [None] * n
    if n <= RSI_PERIOD:
        return result

    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, RSI_PERIOD + 1):
        delta = closes[i] - closes[i - 1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))
    avg_gain = sum(gains) / RSI_PERIOD
    avg_loss = sum(losses) / RSI_PERIOD
    result[RSI_PERIOD] = _rsi_from_averages(avg_gain, avg_loss)

    for i in range(RSI_PERIOD + 1, n):
        delta = closes[i] - closes[i - 1]
        gain = max(delta, 0.0)
        loss = max(-delta, 0.0)
        avg_gain = (avg_gain * (RSI_PERIOD - 1) + gain) / RSI_PERIOD
        avg_loss = (avg_loss * (RSI_PERIOD - 1) + loss) / RSI_PERIOD
        result[i] = _rsi_from_averages(avg_gain, avg_loss)

    return result


def score_rsi(closes: list[float]) -> IndicatorResult:
    """Score the RSI indicator from a list of closing prices, oldest first.

    Requires at least MINIMUM_CLOSES_REQUIRED closes.
    """
    if len(closes) < MINIMUM_CLOSES_REQUIRED:
        raise ValueError(
            f"score_rsi needs at least {MINIMUM_CLOSES_REQUIRED} closes, got {len(closes)}"
        )

    series = _rsi_series(closes)
    current = series[-1]
    prior = series[-1 - SLOPE_LOOKBACK_DAYS]
    assert current is not None
    assert prior is not None

    score = 0
    reasons: list[str] = []

    # 1. RSI vs midline
    if current > MIDLINE:
        score += 1
        reasons.append(f"RSI ({current:.1f}) is above the midline of {MIDLINE:.0f} (+1)")
    else:
        score -= 1
        reasons.append(f"RSI ({current:.1f}) is below the midline of {MIDLINE:.0f} (-1)")

    # 2. Overbought / oversold
    if current >= OVERBOUGHT:
        score -= 1
        reasons.append(
            f"RSI is in overbought territory (>= {OVERBOUGHT:.0f}), a reversal-risk caution (-1)"
        )
    elif current <= OVERSOLD:
        score += 1
        reasons.append(
            f"RSI is in oversold territory (<= {OVERSOLD:.0f}), a reversal-opportunity flag (+1)"
        )

    # 3. RSI slope
    if current > prior:
        score += 1
        reasons.append(f"RSI is rising vs {SLOPE_LOOKBACK_DAYS} trading days ago (+1)")
    elif current < prior:
        score -= 1
        reasons.append(f"RSI is falling vs {SLOPE_LOOKBACK_DAYS} trading days ago (-1)")

    # 4. Recent midline cross within the lookback window
    window = [v for v in series[-(CROSSOVER_LOOKBACK_DAYS + 1) :] if v is not None]
    crossed_up = any(a <= MIDLINE < b for a, b in zip(window, window[1:], strict=False))
    crossed_down = any(a >= MIDLINE > b for a, b in zip(window, window[1:], strict=False))
    if crossed_up:
        score += 1
        reasons.append(
            f"RSI crossed above {MIDLINE:.0f} within the last "
            f"{CROSSOVER_LOOKBACK_DAYS} trading days (+1)"
        )
    elif crossed_down:
        score -= 1
        reasons.append(
            f"RSI crossed below {MIDLINE:.0f} within the last "
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
        values={"rsi": round(current, 4)},
    )
