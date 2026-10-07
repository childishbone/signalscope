"""CANSLIM letter L: is the stock a leader relative to its market?

O'Neil's own "RS Rating" ranks a stock's price performance against every
other stock in the market (percentile 1-99) -- replicating that exactly
would need a full market universe of price data, which this app doesn't
have. This is a simplified stand-in: does the stock's trailing return
beat its own market's benchmark index over the same lookback window.
Beating the benchmark at all is treated as "leading"; this is a looser
bar than IBD's top-20% cutoff, and is documented as such.
"""

from __future__ import annotations

from signalscope.signals.canslim_types import CanslimLetterResult, CanslimVerdict

LOOKBACK_WINDOW = 252  # ~1 trading year
MINIMUM_CLOSES_REQUIRED = 60


def _total_return_pct(closes: list[float]) -> float:
    window = closes[-LOOKBACK_WINDOW:]
    return (window[-1] / window[0] - 1) * 100


def score_relative_strength(
    security_closes: list[float],
    benchmark_closes: list[float],
    benchmark_symbol: str,
) -> CanslimLetterResult:
    """Score letter L by comparing trailing total return to a benchmark index.

    Each series uses up to LOOKBACK_WINDOW of its own available closes
    (oldest first); shorter histories still work, down to
    MINIMUM_CLOSES_REQUIRED.
    """
    if (
        len(security_closes) < MINIMUM_CLOSES_REQUIRED
        or len(benchmark_closes) < MINIMUM_CLOSES_REQUIRED
    ):
        return CanslimLetterResult(
            letter="L",
            verdict=CanslimVerdict.INSUFFICIENT_DATA,
            reasons=[
                f"Need at least {MINIMUM_CLOSES_REQUIRED} trading days of both the "
                f"security's and {benchmark_symbol}'s price history"
            ],
        )

    security_return = _total_return_pct(security_closes)
    benchmark_return = _total_return_pct(benchmark_closes)
    excess_return = security_return - benchmark_return

    if excess_return > 0:
        verdict = CanslimVerdict.PASS
        reasons = [
            f"Outperforming {benchmark_symbol}: {security_return:.1f}% vs "
            f"{benchmark_return:.1f}% over the trailing window (+{excess_return:.1f} pts)"
        ]
    else:
        verdict = CanslimVerdict.FAIL
        reasons = [
            f"Underperforming {benchmark_symbol}: {security_return:.1f}% vs "
            f"{benchmark_return:.1f}% over the trailing window ({excess_return:.1f} pts)"
        ]

    return CanslimLetterResult(
        letter="L",
        verdict=verdict,
        reasons=reasons,
        values={
            "security_return_pct": round(security_return, 2),
            "benchmark_return_pct": round(benchmark_return, 2),
            "excess_return_pct": round(excess_return, 2),
        },
    )
