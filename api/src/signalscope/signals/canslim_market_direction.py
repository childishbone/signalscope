"""CANSLIM letter M: is the overall market in a confirmed uptrend?

Reuses the existing DMA trend classification (score_dma), applied to a
market's benchmark index rather than an individual security -- O'Neil's
"M" is explicitly about the market as a whole, not stock-specific. All
securities trading in the same market share one M verdict.
"""

from __future__ import annotations

from signalscope.signals.canslim_types import CanslimLetterResult, CanslimVerdict
from signalscope.signals.dma import MINIMUM_CLOSES_REQUIRED, score_dma
from signalscope.signals.types import SignalState


def score_market_direction(index_closes: list[float], index_symbol: str) -> CanslimLetterResult:
    """Score letter M from a benchmark index's closing prices, oldest first."""
    if len(index_closes) < MINIMUM_CLOSES_REQUIRED:
        return CanslimLetterResult(
            letter="M",
            verdict=CanslimVerdict.INSUFFICIENT_DATA,
            reasons=[
                f"Need at least {MINIMUM_CLOSES_REQUIRED} trading days of {index_symbol} "
                f"history, got {len(index_closes)}"
            ],
        )

    dma_result = score_dma(index_closes)

    if dma_result.state == SignalState.BEARISH:
        verdict = CanslimVerdict.FAIL
        headline = (
            f"{index_symbol} is in a confirmed downtrend -- O'Neil's playbook calls for "
            "raising cash rather than buying into market weakness"
        )
    else:
        trend_word = (
            "a confirmed uptrend"
            if dma_result.state == SignalState.BULLISH
            else "no clear downtrend"
        )
        verdict = CanslimVerdict.PASS
        headline = f"{index_symbol} is showing {trend_word}"

    return CanslimLetterResult(
        letter="M",
        verdict=verdict,
        reasons=[headline, *dma_result.reasons],
        values={**dma_result.values, "dma_score": float(dma_result.score)},
    )
