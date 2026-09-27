"""Ichimoku Cloud (Ichimoku Kinko Hyo) indicator.

Classifies a security as Bullish, Neutral, or Bearish using the four
checks traditionally used to read an Ichimoku chart. Each check is a
deterministic comparison of prices or lines that already exist on the
chart -- nothing here is invented beyond picking a scoring convention for
each comparison.

Components (all derived from rolling high/low midpoints, a technique
sometimes called a Donchian midpoint):
  Tenkan-sen (Conversion Line)  -- midpoint of the 9-period high/low
  Kijun-sen (Base Line)         -- midpoint of the 26-period high/low
  Senkou Span A (Leading Span A) -- midpoint of Tenkan/Kijun, plotted
                                     DISPLACEMENT periods ahead
  Senkou Span B (Leading Span B) -- midpoint of the 52-period high/low,
                                     plotted DISPLACEMENT periods ahead
  Chikou Span (Lagging Span)    -- today's close, plotted DISPLACEMENT
                                     periods behind

Scoring rules (each contributes -1, 0, or +1 to the score):
  1. Price vs the cloud (the Senkou A/B pair visible at today's position,
     which were actually computed DISPLACEMENT periods ago) -- above both
     spans is bullish, below both is bearish, inside the cloud is neutral
  2. Cloud colour -- Senkou A above Senkou B is a bullish ("green") cloud,
     below is bearish ("red")
  3. Tenkan-sen vs Kijun-sen -- the short line above the medium line is
     bullish momentum, below is bearish
  4. Chikou Span confirmation -- is today's close above or below the
     close from DISPLACEMENT periods ago (the price the lagging span is
     now sitting next to)

Final score >= BULLISH_THRESHOLD -> Bullish
Final score <= BEARISH_THRESHOLD -> Bearish
otherwise                        -> Neutral
"""

from __future__ import annotations

from signalscope.signals.types import IndicatorResult, SignalState

TENKAN_PERIOD = 9
KIJUN_PERIOD = 26
SENKOU_B_PERIOD = 52
DISPLACEMENT = 26

BULLISH_THRESHOLD = 2
BEARISH_THRESHOLD = -2

# The cloud visible "today" was computed DISPLACEMENT periods ago, and
# that computation itself needs a full SENKOU_B_PERIOD window of history.
MINIMUM_BARS_REQUIRED = SENKOU_B_PERIOD + DISPLACEMENT


def _donchian_mid(highs: list[float], lows: list[float], period: int, end: int) -> float:
    """Midpoint of the highest high and lowest low over `period` bars
    ending at index `end` (exclusive), i.e. highs[end - period : end]."""
    window_high = max(highs[end - period : end])
    window_low = min(lows[end - period : end])
    return (window_high + window_low) / 2


def score_ichimoku(highs: list[float], lows: list[float], closes: list[float]) -> IndicatorResult:
    """Score the Ichimoku Cloud indicator from parallel high/low/close
    lists, oldest first. Requires at least MINIMUM_BARS_REQUIRED bars."""
    if not (len(highs) == len(lows) == len(closes)):
        raise ValueError("highs, lows, and closes must be the same length")
    if len(closes) < MINIMUM_BARS_REQUIRED:
        raise ValueError(
            f"score_ichimoku needs at least {MINIMUM_BARS_REQUIRED} bars, got {len(closes)}"
        )

    n = len(closes)
    price = closes[-1]

    tenkan_today = _donchian_mid(highs, lows, TENKAN_PERIOD, n)
    kijun_today = _donchian_mid(highs, lows, KIJUN_PERIOD, n)

    # The cloud "at today's position" was projected DISPLACEMENT periods
    # ago, so it's computed from data ending at that earlier point.
    past_end = n - DISPLACEMENT
    tenkan_past = _donchian_mid(highs, lows, TENKAN_PERIOD, past_end)
    kijun_past = _donchian_mid(highs, lows, KIJUN_PERIOD, past_end)
    senkou_a_today = (tenkan_past + kijun_past) / 2
    senkou_b_today = _donchian_mid(highs, lows, SENKOU_B_PERIOD, past_end)

    cloud_top = max(senkou_a_today, senkou_b_today)
    cloud_bottom = min(senkou_a_today, senkou_b_today)

    price_displacement_ago = closes[-(DISPLACEMENT + 1)]

    score = 0
    reasons: list[str] = []

    # 1. Price vs cloud
    if price > cloud_top:
        score += 1
        reasons.append("Price is above the cloud (+1)")
    elif price < cloud_bottom:
        score -= 1
        reasons.append("Price is below the cloud (-1)")
    else:
        reasons.append("Price is inside the cloud, no clear trend (0)")

    # 2. Cloud colour
    if senkou_a_today > senkou_b_today:
        score += 1
        reasons.append("The cloud ahead is bullish (Senkou A above Senkou B) (+1)")
    elif senkou_a_today < senkou_b_today:
        score -= 1
        reasons.append("The cloud ahead is bearish (Senkou A below Senkou B) (-1)")
    else:
        reasons.append("The cloud is flat, Senkou A equals Senkou B (0)")

    # 3. Tenkan-sen vs Kijun-sen
    if tenkan_today > kijun_today:
        score += 1
        reasons.append("Tenkan-sen is above Kijun-sen, short-term momentum is up (+1)")
    elif tenkan_today < kijun_today:
        score -= 1
        reasons.append("Tenkan-sen is below Kijun-sen, short-term momentum is down (-1)")
    else:
        reasons.append("Tenkan-sen equals Kijun-sen (0)")

    # 4. Chikou Span confirmation
    if price > price_displacement_ago:
        score += 1
        reasons.append(
            f"Chikou Span confirms the uptrend: price is above the close from "
            f"{DISPLACEMENT} periods ago (+1)"
        )
    elif price < price_displacement_ago:
        score -= 1
        reasons.append(
            f"Chikou Span confirms the downtrend: price is below the close from "
            f"{DISPLACEMENT} periods ago (-1)"
        )
    else:
        reasons.append("Chikou Span is unchanged from the price it's compared against (0)")

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
            "tenkan": round(tenkan_today, 4),
            "kijun": round(kijun_today, 4),
            "senkou_a": round(senkou_a_today, 4),
            "senkou_b": round(senkou_b_today, 4),
            "chikou_reference_price": round(price_displacement_ago, 4),
        },
    )
