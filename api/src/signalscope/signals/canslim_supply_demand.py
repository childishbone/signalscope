"""CANSLIM letter S: supply and demand -- is volume confirming accumulation?

O'Neil wants to see volume expand on up days and contract on down days
(institutions quietly accumulating), rather than heavy volume on sell-offs
(distribution). This compares average volume on up days vs down days over
the lookback window. Buyback-driven float shrinkage -- the other half of
"supply and demand" -- isn't included: shares-outstanding data is too
unreliable outside the US to build on confidently.
"""

from __future__ import annotations

from signalscope.signals.canslim_types import CanslimLetterResult, CanslimVerdict

LOOKBACK_WINDOW = 50  # trading days (~10 weeks)
MINIMUM_CLOSES_REQUIRED = LOOKBACK_WINDOW + 1
MINIMUM_SAMPLES_PER_SIDE = 5  # need at least this many up days and down days to trust the average


def score_supply_demand(closes: list[float], volumes: list[int]) -> CanslimLetterResult:
    """Score letter S from aligned closes and volumes, oldest first."""
    if len(closes) < MINIMUM_CLOSES_REQUIRED or len(volumes) < MINIMUM_CLOSES_REQUIRED:
        return CanslimLetterResult(
            letter="S",
            verdict=CanslimVerdict.INSUFFICIENT_DATA,
            reasons=[
                f"Need at least {MINIMUM_CLOSES_REQUIRED} trading days of price and volume history"
            ],
        )

    window_closes = closes[-MINIMUM_CLOSES_REQUIRED:]
    window_volumes = volumes[-MINIMUM_CLOSES_REQUIRED:]

    up_volumes: list[int] = []
    down_volumes: list[int] = []
    for i in range(1, len(window_closes)):
        if window_closes[i] > window_closes[i - 1]:
            up_volumes.append(window_volumes[i])
        elif window_closes[i] < window_closes[i - 1]:
            down_volumes.append(window_volumes[i])

    if len(up_volumes) < MINIMUM_SAMPLES_PER_SIDE or len(down_volumes) < MINIMUM_SAMPLES_PER_SIDE:
        return CanslimLetterResult(
            letter="S",
            verdict=CanslimVerdict.INSUFFICIENT_DATA,
            reasons=[
                f"Need at least {MINIMUM_SAMPLES_PER_SIDE} up days and "
                f"{MINIMUM_SAMPLES_PER_SIDE} down days in the last {LOOKBACK_WINDOW} "
                f"trading days, got {len(up_volumes)} up / {len(down_volumes)} down"
            ],
        )

    avg_up_volume = sum(up_volumes) / len(up_volumes)
    avg_down_volume = sum(down_volumes) / len(down_volumes)
    ratio = avg_up_volume / avg_down_volume

    if ratio > 1.0:
        verdict = CanslimVerdict.PASS
        reasons = [
            f"Average volume on up days ({avg_up_volume:,.0f}) exceeds average volume "
            f"on down days ({avg_down_volume:,.0f}) over the last {LOOKBACK_WINDOW} "
            f"trading days -- ratio {ratio:.2f}"
        ]
    else:
        verdict = CanslimVerdict.FAIL
        reasons = [
            f"Average volume on down days ({avg_down_volume:,.0f}) exceeds average "
            f"volume on up days ({avg_up_volume:,.0f}) over the last {LOOKBACK_WINDOW} "
            f"trading days -- ratio {ratio:.2f}"
        ]

    return CanslimLetterResult(
        letter="S",
        verdict=verdict,
        reasons=reasons,
        values={
            "avg_up_volume": round(avg_up_volume, 2),
            "avg_down_volume": round(avg_down_volume, 2),
            "up_down_volume_ratio": round(ratio, 4),
            "up_days": len(up_volumes),
            "down_days": len(down_volumes),
        },
    )
