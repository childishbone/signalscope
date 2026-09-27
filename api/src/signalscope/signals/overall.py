"""The Overall signal: a weighted combination of the four indicators.

Every indicator's state is first normalised onto the same -2 to +2 scale
(Bullish = +2, Neutral = 0, Bearish = -2), regardless of how each
indicator's own internal scoring works. Each indicator is then given a
configurable weight, and the Overall score is the weighted average of
the four normalised scores -- which stays within -2 to +2 as long as
weights are non-negative.

Weights (all in WEIGHTS below, easy to tune without touching the logic):
  DMA, RSI, and Ichimoku each get a weight of 1.0 -- they're all
  well-established, rule-based technical indicators.
  Elliott Wave gets a weight of 0.5 -- deliberately half the others,
  because it is the one indicator that is a heuristic estimate rather
  than an objective reading of the chart (see signals/elliott.py). This
  ensures Elliott Wave alone can never push the Overall signal into
  Bullish or Bearish; it can only nudge a signal the other three
  indicators already lean toward.

Final weighted average >= BULLISH_THRESHOLD -> Bullish
Final weighted average <= BEARISH_THRESHOLD -> Bearish
otherwise                                    -> Neutral

Thresholds are set at half of the max possible per-indicator score (1.0
out of a possible 2.0), the same "half of max magnitude" convention used
by every other indicator's own internal threshold.
"""

from __future__ import annotations

from signalscope.signals.types import IndicatorResult, SignalState

STATE_SCORE: dict[SignalState, float] = {
    SignalState.BULLISH: 2.0,
    SignalState.NEUTRAL: 0.0,
    SignalState.BEARISH: -2.0,
}

WEIGHT_DMA = 1.0
WEIGHT_RSI = 1.0
WEIGHT_ICHIMOKU = 1.0
WEIGHT_ELLIOTT = 0.5

BULLISH_THRESHOLD = 1.0
BEARISH_THRESHOLD = -1.0


def compute_overall(
    dma: IndicatorResult,
    rsi: IndicatorResult,
    ichimoku: IndicatorResult,
    elliott: IndicatorResult,
) -> IndicatorResult:
    """Combine the four indicator results into one Overall signal."""
    weighted_indicators = [
        ("DMA", dma, WEIGHT_DMA),
        ("RSI", rsi, WEIGHT_RSI),
        ("Ichimoku", ichimoku, WEIGHT_ICHIMOKU),
        ("Elliott Wave", elliott, WEIGHT_ELLIOTT),
    ]

    total_weight = sum(weight for _, _, weight in weighted_indicators)
    weighted_sum = sum(
        STATE_SCORE[result.state] * weight for _, result, weight in weighted_indicators
    )
    weighted_average = weighted_sum / total_weight

    reasons: list[str] = []
    for name, result, weight in weighted_indicators:
        contribution = STATE_SCORE[result.state] * weight
        reasons.append(
            f"{name}: {result.state.value.capitalize()} "
            f"(weight {weight:g}, contributes {contribution:+.1f})"
        )
    reasons.append(f"Weighted average score: {weighted_average:+.2f} (out of a possible +/-2.00)")

    if weighted_average >= BULLISH_THRESHOLD:
        state = SignalState.BULLISH
    elif weighted_average <= BEARISH_THRESHOLD:
        state = SignalState.BEARISH
    else:
        state = SignalState.NEUTRAL

    return IndicatorResult(
        state=state,
        score=round(weighted_average, 4),
        reasons=reasons,
        values={
            "dma_contribution": round(STATE_SCORE[dma.state] * WEIGHT_DMA, 4),
            "rsi_contribution": round(STATE_SCORE[rsi.state] * WEIGHT_RSI, 4),
            "ichimoku_contribution": round(STATE_SCORE[ichimoku.state] * WEIGHT_ICHIMOKU, 4),
            "elliott_contribution": round(STATE_SCORE[elliott.state] * WEIGHT_ELLIOTT, 4),
            "weighted_average": round(weighted_average, 4),
        },
    )
