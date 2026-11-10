"""Research-only candidate indicators for the backtest.

These are NOT used by the live app. They exist so new ideas can be tested
with the same walk-forward backtest as the real indicators, and only moved
into src/signalscope/signals/ (with proper tests) if they earn it.

Each scorer takes closes (oldest first) and returns an IndicatorResult in
the same shape as the live indicators.

  52-week high  -- how close price is to its highest close of the past year.
                   Stocks near a 52-week high have historically tended to
                   keep outperforming (George & Hwang, 2004).
  Momentum      -- return over the past year, skipping the most recent
                   month (the classic "12-1" momentum measure).
  Volatility    -- is recent 20-day volatility calm or turbulent compared
                   with its own past year? A risk gauge: Bullish = calm,
                   Bearish = turbulent.
"""

from __future__ import annotations

from signalscope.signals.types import IndicatorResult, SignalState

HIGH_WINDOW = 252
HIGH_BULLISH_RATIO = 0.95
HIGH_BEARISH_RATIO = 0.70
HIGH52_MINIMUM = HIGH_WINDOW

MOMENTUM_LOOKBACK = 252
MOMENTUM_SKIP = 21
MOMENTUM_BULLISH = 0.10
MOMENTUM_BEARISH = -0.10
MOMENTUM_MINIMUM = MOMENTUM_LOOKBACK + 1

VOL_WINDOW = 20
VOL_HISTORY = 252
VOL_CALM_PERCENTILE = 20.0
VOL_TURBULENT_PERCENTILE = 80.0
VOLATILITY_MINIMUM = VOL_WINDOW + VOL_HISTORY + 1


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def score_high52(closes: list[float]) -> IndicatorResult:
    if len(closes) < HIGH52_MINIMUM:
        raise ValueError(f"score_high52 needs at least {HIGH52_MINIMUM} closes")
    ratio = closes[-1] / max(closes[-HIGH_WINDOW:])
    score = _clamp(int(ratio * 10) - 8, -4, 2)
    if ratio >= HIGH_BULLISH_RATIO:
        state = SignalState.BULLISH
    elif ratio <= HIGH_BEARISH_RATIO:
        state = SignalState.BEARISH
    else:
        state = SignalState.NEUTRAL
    return IndicatorResult(
        state=state,
        score=score,
        reasons=[f"Price is {ratio * 100:.0f}% of its 52-week high"],
        values={"pct_of_52w_high": round(ratio * 100, 2)},
    )


def score_momentum(closes: list[float]) -> IndicatorResult:
    if len(closes) < MOMENTUM_MINIMUM:
        raise ValueError(f"score_momentum needs at least {MOMENTUM_MINIMUM} closes")
    ret = closes[-1 - MOMENTUM_SKIP] / closes[-1 - MOMENTUM_LOOKBACK] - 1.0
    score = _clamp(round(ret / MOMENTUM_BULLISH), -4, 4)
    if ret >= MOMENTUM_BULLISH:
        state = SignalState.BULLISH
    elif ret <= MOMENTUM_BEARISH:
        state = SignalState.BEARISH
    else:
        state = SignalState.NEUTRAL
    return IndicatorResult(
        state=state,
        score=score,
        reasons=[f"12-month return excluding the last month: {ret * 100:+.1f}%"],
        values={"momentum_12_1_pct": round(ret * 100, 2)},
    )


def _rolling_volatilities(closes: list[float]) -> list[float]:
    """Daily-return standard deviation over each of the last VOL_HISTORY
    windows of VOL_WINDOW returns, oldest first."""
    n = len(closes)
    count = VOL_HISTORY + VOL_WINDOW - 1
    rets = [closes[i] / closes[i - 1] - 1.0 for i in range(n - count, n)]
    prefix = [0.0]
    prefix_sq = [0.0]
    for r in rets:
        prefix.append(prefix[-1] + r)
        prefix_sq.append(prefix_sq[-1] + r * r)
    vols: list[float] = []
    for end in range(VOL_WINDOW, count + 1):
        total = prefix[end] - prefix[end - VOL_WINDOW]
        total_sq = prefix_sq[end] - prefix_sq[end - VOL_WINDOW]
        variance = max(0.0, (total_sq - total * total / VOL_WINDOW) / (VOL_WINDOW - 1))
        vols.append(variance**0.5)
    return vols


def score_volatility(closes: list[float]) -> IndicatorResult:
    if len(closes) < VOLATILITY_MINIMUM:
        raise ValueError(f"score_volatility needs at least {VOLATILITY_MINIMUM} closes")
    vols = _rolling_volatilities(closes)
    current = vols[-1]
    percentile = 100.0 * sum(1 for v in vols if v <= current) / len(vols)
    if percentile <= VOL_CALM_PERCENTILE:
        state = SignalState.BULLISH
    elif percentile >= VOL_TURBULENT_PERCENTILE:
        state = SignalState.BEARISH
    else:
        state = SignalState.NEUTRAL
    score = 2 - _clamp(int(percentile // 20), 0, 4)
    return IndicatorResult(
        state=state,
        score=score,
        reasons=[
            f"20-day volatility is {current * (252**0.5) * 100:.0f}% annualised, "
            f"higher than {percentile:.0f}% of the past year"
        ],
        values={
            "volatility_annualised_pct": round(current * (252**0.5) * 100, 2),
            "volatility_percentile": round(percentile, 1),
        },
    )
