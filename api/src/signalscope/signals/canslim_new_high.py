"""CANSLIM letter N: is the stock at or near a new high?

O'Neil wants stocks breaking out to new highs out of a proper base, on
volume. This is a simplified technical proxy for that: how close is the
current price to its highest close over the lookback window. Volume
confirmation is handled separately, under letter S.
"""

from __future__ import annotations

from signalscope.signals.canslim_types import CanslimLetterResult, CanslimVerdict

LOOKBACK_WINDOW = 252  # ~1 trading year
MINIMUM_CLOSES_REQUIRED = 60  # need a meaningful window, even if shorter than a full year
NEW_HIGH_THRESHOLD_PCT = 15.0  # O'Neil: look for names within ~15% of a new high


def score_new_high(closes: list[float]) -> CanslimLetterResult:
    """Score letter N from a list of closing prices, oldest first.

    Uses up to LOOKBACK_WINDOW closes (shorter history still works, and
    is noted in the reasons -- a 90-day high is a weaker claim than a
    252-day one, but still meaningful). Returns INSUFFICIENT_DATA if
    there isn't even MINIMUM_CLOSES_REQUIRED of history.
    """
    if len(closes) < MINIMUM_CLOSES_REQUIRED:
        return CanslimLetterResult(
            letter="N",
            verdict=CanslimVerdict.INSUFFICIENT_DATA,
            reasons=[
                f"Need at least {MINIMUM_CLOSES_REQUIRED} trading days of price "
                f"history, got {len(closes)}"
            ],
        )

    window = closes[-LOOKBACK_WINDOW:]
    price = closes[-1]
    high = max(window)
    pct_below_high = (high - price) / high * 100

    if pct_below_high <= NEW_HIGH_THRESHOLD_PCT:
        verdict = CanslimVerdict.PASS
        reasons = [
            f"Price (${price:.2f}) is within {NEW_HIGH_THRESHOLD_PCT:.0f}% of its "
            f"{len(window)}-trading-day high (${high:.2f}) -- {pct_below_high:.1f}% below"
        ]
    else:
        verdict = CanslimVerdict.FAIL
        reasons = [
            f"Price (${price:.2f}) is {pct_below_high:.1f}% below its "
            f"{len(window)}-trading-day high (${high:.2f}), more than the "
            f"{NEW_HIGH_THRESHOLD_PCT:.0f}% threshold"
        ]

    return CanslimLetterResult(
        letter="N",
        verdict=verdict,
        reasons=reasons,
        values={
            "price": round(price, 4),
            "high": round(high, 4),
            "pct_below_high": round(pct_below_high, 2),
            "window_days": len(window),
        },
    )
