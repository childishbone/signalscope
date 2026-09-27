"""Algorithmic Elliott Wave Estimate.

IMPORTANT: unlike DMA, RSI, and Ichimoku, this indicator is explicitly
NOT presented as an objective reading of the market. Elliott Wave theory
is a subjective form of pattern recognition even among professional
chartists -- two experienced analysts can label the same chart
differently. What follows is a deterministic, rule-based *heuristic* that
makes one arbitrary but transparent set of choices, checks its own count
against a couple of classic Elliott guidelines, and openly defaults to
"Neutral, low confidence" whenever those guidelines are violated or the
data doesn't support a confident read. It should be displayed to users
with that framing front and centre, never as a prediction.

How it works:
  1. A "zigzag" filter walks the closing-price series and records a pivot
     only when price reverses by at least ZIGZAG_THRESHOLD_PCT from the
     running extreme, discarding smaller wiggles as noise.
  2. The most recent up to 5 confirmed swings are tentatively labelled as
     waves 1 through 5 of a fresh impulse sequence. This is itself an
     assumption -- the algorithm has no way to know the true larger-degree
     wave count, so it always restarts the count from the most recent
     handful of swings.
  3. Two classic Elliott guidelines are checked: wave 2 must not retrace
     beyond the start of wave 1, and wave 3 must not be the shortest of
     waves 1, 3, and 5. If either is violated, the count doesn't fit even
     loose Elliott rules, and the result is Neutral with an explanation.
  4. If the count passes those checks, the current wave position decides
     the read: an odd-numbered wave (1 or 3) in progress leans in that
     wave's direction; an even-numbered wave (2 or 4) is a corrective
     pullback and is called Neutral; a completed wave 5 is also called
     Neutral, since classic theory expects a corrective A-B-C move next.

Known, deliberate limitation: a 3-wave corrective sequence (A-B-C) is
structurally identical to the first 3 waves of a fresh 5-wave impulse --
both are just "up, down, up" (or the reverse). This heuristic cannot
tell them apart with only past price data; it always assumes the
impulse interpretation. Only later price action reveals which one it
actually was. This is disclosed to the user rather than concealed.
"""

from __future__ import annotations

from signalscope.signals.types import IndicatorResult, SignalState

ZIGZAG_THRESHOLD_PCT = 0.05

# Not a strict mathematical requirement like the other indicators' fixed
# windows -- just enough history that the zigzag filter has a realistic
# chance of finding several genuine swings.
MINIMUM_CLOSES_REQUIRED = 60

DISCLAIMER = (
    "This is an algorithmic heuristic estimate of Elliott Wave position, "
    "not an objective fact. Elliott Wave analysis is inherently subjective, "
    "and this count could be reinterpreted as new price data arrives."
)


def _find_zigzag_pivots(closes: list[float], threshold_pct: float) -> list[tuple[int, float]]:
    """Record a pivot only after price reverses by at least `threshold_pct`
    from the running extreme. Always includes the series' starting point
    as the first pivot, so the very first wave has a reference start."""
    if not closes:
        return []
    if len(closes) == 1:
        return [(0, closes[0])]

    pivots: list[tuple[int, float]] = [(0, closes[0])]
    anchor_price = closes[0]
    up_idx, up_price = 0, closes[0]
    down_idx, down_price = 0, closes[0]
    direction: str | None = None
    extreme_idx, extreme_price = 0, closes[0]

    for i in range(1, len(closes)):
        price = closes[i]
        if direction is None:
            if price > up_price:
                up_idx, up_price = i, price
            if price < down_price:
                down_idx, down_price = i, price
            if up_price >= anchor_price * (1 + threshold_pct):
                direction = "up"
                extreme_idx, extreme_price = up_idx, up_price
            elif down_price <= anchor_price * (1 - threshold_pct):
                direction = "down"
                extreme_idx, extreme_price = down_idx, down_price
        elif direction == "up":
            if price >= extreme_price:
                extreme_idx, extreme_price = i, price
            elif price <= extreme_price * (1 - threshold_pct):
                pivots.append((extreme_idx, extreme_price))
                direction = "down"
                extreme_idx, extreme_price = i, price
        else:
            if price <= extreme_price:
                extreme_idx, extreme_price = i, price
            elif price >= extreme_price * (1 + threshold_pct):
                pivots.append((extreme_idx, extreme_price))
                direction = "up"
                extreme_idx, extreme_price = i, price

    if extreme_idx != pivots[-1][0]:
        pivots.append((extreme_idx, extreme_price))
    return pivots


def score_elliott_wave(closes: list[float]) -> IndicatorResult:
    """Estimate the current Elliott Wave position from a list of closing
    prices, oldest first. Requires at least MINIMUM_CLOSES_REQUIRED closes.

    See the module docstring for the full, important caveats. This is a
    heuristic estimate, not a claim about the true wave count.
    """
    if len(closes) < MINIMUM_CLOSES_REQUIRED:
        raise ValueError(
            f"score_elliott_wave needs at least {MINIMUM_CLOSES_REQUIRED} closes, got {len(closes)}"
        )

    pivots = _find_zigzag_pivots(closes, ZIGZAG_THRESHOLD_PCT)
    legs = pivots[-6:]  # up to 5 legs = 6 pivot points, including the start

    reasons: list[str] = [DISCLAIMER]

    if len(legs) < 4:  # need at least waves 1, 2, 3 (4 pivot points)
        reasons.append(
            "Not enough distinct price swings were found to attempt a wave "
            "count; defaulting to Neutral."
        )
        return IndicatorResult(
            state=SignalState.NEUTRAL,
            score=0,
            reasons=reasons,
            values={"wave_position": 0.0, "pattern_valid": 0.0},
        )

    magnitudes = [abs(legs[i][1] - legs[i - 1][1]) for i in range(1, len(legs))]
    directions = ["up" if legs[i][1] > legs[i - 1][1] else "down" for i in range(1, len(legs))]
    wave_position = len(legs) - 1

    reasons.append(
        f"Identified {wave_position} recent price swing(s) using a "
        f"{ZIGZAG_THRESHOLD_PCT:.0%} zigzag filter, tentatively labelled as "
        f"waves 1-{wave_position} of a fresh impulse sequence."
    )

    wave1_start_price = legs[0][1]
    wave2_end_price = legs[2][1] if len(legs) > 2 else None
    pattern_valid = True

    if wave2_end_price is not None:
        if directions[0] == "up" and wave2_end_price <= wave1_start_price:
            pattern_valid = False
            reasons.append(
                "Rule violation: wave 2 retraced beyond the start of wave 1, so "
                "this does not fit a valid Elliott impulse -- treating as "
                "low-confidence."
            )
        elif directions[0] == "down" and wave2_end_price >= wave1_start_price:
            pattern_valid = False
            reasons.append(
                "Rule violation: wave 2 retraced beyond the start of wave 1, so "
                "this does not fit a valid Elliott impulse -- treating as "
                "low-confidence."
            )

    if wave_position >= 3:
        wave1_len = magnitudes[0]
        wave3_len = magnitudes[2]
        wave5_len = magnitudes[4] if wave_position >= 5 else None
        shortest_candidates = [wave1_len] + ([wave5_len] if wave5_len is not None else [])
        if wave3_len < min(shortest_candidates):
            pattern_valid = False
            reasons.append(
                "Rule violation: wave 3 is shorter than both wave 1 and wave 5, "
                "which classic Elliott guidelines say should never happen -- "
                "treating as low-confidence."
            )

    if not pattern_valid:
        return IndicatorResult(
            state=SignalState.NEUTRAL,
            score=0,
            reasons=reasons,
            values={"wave_position": float(wave_position), "pattern_valid": 0.0},
        )

    last_direction = directions[-1]

    if wave_position in (1, 3):
        state = SignalState.BULLISH if last_direction == "up" else SignalState.BEARISH
        score = 1 if last_direction == "up" else -1
        reasons.append(
            f"Currently in wave {wave_position}, an impulsive leg in the "
            f"{last_direction} direction -- momentum is expected to continue."
        )
        if wave_position == 3:
            reasons.append(
                "Note: a 3-swing count can equally be an A-B-C correction rather "
                "than an impulse -- these two patterns look identical until later "
                "price action confirms one over the other."
            )
    elif wave_position in (2, 4):
        state = SignalState.NEUTRAL
        score = 0
        reasons.append(
            f"Currently in wave {wave_position}, a corrective pullback -- "
            "direction is unclear until the correction completes."
        )
    else:
        state = SignalState.NEUTRAL
        score = 0
        reasons.append(
            f"Wave 5 appears complete after a {last_direction} impulse -- classic "
            "Elliott theory expects a corrective A-B-C retracement next, so "
            "directional confidence is low despite the recent move."
        )

    return IndicatorResult(
        state=state,
        score=score,
        reasons=reasons,
        values={"wave_position": float(wave_position), "pattern_valid": 1.0},
    )
