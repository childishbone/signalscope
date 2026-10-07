"""CANSLIM letters C and A: current-quarter and annual EPS growth.

O'Neil's own thresholds (25%+ current-quarter growth, 25%+ annual growth
sustained over several years) are used as sensible defaults; they're named
constants so they can be tuned later. EPS history is frequently sparse or
irregular outside the US (see README limitations), so both scorers match
periods by calendar proximity rather than assuming evenly-spaced data, and
resolve to INSUFFICIENT_DATA rather than guessing when the data isn't there.
"""

from __future__ import annotations

from datetime import timedelta

from signalscope.market_data.types import EpsPeriod
from signalscope.signals.canslim_types import CanslimLetterResult, CanslimVerdict

CURRENT_QUARTER_GROWTH_THRESHOLD_PCT = 25.0
YOY_QUARTER_MATCH_TOLERANCE_DAYS = 45

ANNUAL_PERIODS_REQUIRED = 3
ANNUAL_GROWTH_THRESHOLD_PCT = 25.0
ANNUAL_DECLINE_TOLERANCE_PCT = -10.0  # one rough year is tolerated; a worse one isn't


def _pct_growth(prior: float, current: float) -> float | None:
    """None when the prior period wasn't positive -- percent growth off a
    loss (or exactly zero) isn't a meaningful number."""
    if prior <= 0:
        return None
    return (current - prior) / prior * 100


def score_current_earnings_growth(quarterly_eps: list[EpsPeriod]) -> CanslimLetterResult:
    """Score letter C: current-quarter EPS vs the same quarter a year ago."""
    if not quarterly_eps:
        return CanslimLetterResult(
            letter="C",
            verdict=CanslimVerdict.INSUFFICIENT_DATA,
            reasons=["No quarterly EPS data available"],
        )

    current = quarterly_eps[-1]
    target_date = current.period_end - timedelta(days=365)
    candidates = quarterly_eps[:-1]

    year_ago = min(candidates, key=lambda p: abs((p.period_end - target_date).days), default=None)
    if (
        year_ago is None
        or abs((year_ago.period_end - target_date).days) > YOY_QUARTER_MATCH_TOLERANCE_DAYS
    ):
        return CanslimLetterResult(
            letter="C",
            verdict=CanslimVerdict.INSUFFICIENT_DATA,
            reasons=[
                "No quarterly EPS reported roughly one year before the current "
                f"quarter ({current.period_end})"
            ],
        )

    growth = _pct_growth(year_ago.eps, current.eps)

    if growth is None:
        if current.eps > 0:
            verdict = CanslimVerdict.PASS
            reasons = [
                f"Turned profitable: EPS was {year_ago.eps:.2f} in the year-ago quarter "
                f"({year_ago.period_end}), now {current.eps:.2f} ({current.period_end})"
            ]
        else:
            verdict = CanslimVerdict.FAIL
            reasons = [
                f"Still unprofitable: EPS was {year_ago.eps:.2f} in the year-ago quarter "
                f"({year_ago.period_end}), now {current.eps:.2f} ({current.period_end})"
            ]
    elif growth >= CURRENT_QUARTER_GROWTH_THRESHOLD_PCT:
        verdict = CanslimVerdict.PASS
        reasons = [
            f"Current-quarter EPS {current.eps:.2f} vs {year_ago.eps:.2f} a year ago "
            f"-- +{growth:.1f}% YoY (threshold: {CURRENT_QUARTER_GROWTH_THRESHOLD_PCT:.0f}%)"
        ]
    else:
        verdict = CanslimVerdict.FAIL
        reasons = [
            f"Current-quarter EPS {current.eps:.2f} vs {year_ago.eps:.2f} a year ago "
            f"-- {growth:+.1f}% YoY, below the "
            f"{CURRENT_QUARTER_GROWTH_THRESHOLD_PCT:.0f}% threshold"
        ]

    return CanslimLetterResult(
        letter="C",
        verdict=verdict,
        reasons=reasons,
        values={
            "current_eps": round(current.eps, 4),
            "year_ago_eps": round(year_ago.eps, 4),
            **({"yoy_growth_pct": round(growth, 2)} if growth is not None else {}),
        },
    )


def score_annual_earnings_growth(annual_eps: list[EpsPeriod]) -> CanslimLetterResult:
    """Score letter A: consistent annual EPS growth over recent years."""
    if len(annual_eps) < ANNUAL_PERIODS_REQUIRED:
        return CanslimLetterResult(
            letter="A",
            verdict=CanslimVerdict.INSUFFICIENT_DATA,
            reasons=[
                f"Need at least {ANNUAL_PERIODS_REQUIRED} years of annual EPS, got "
                f"{len(annual_eps)}"
            ],
        )

    recent = annual_eps[-ANNUAL_PERIODS_REQUIRED:]
    growth_rates: list[float] = []
    for prior, current in zip(recent, recent[1:], strict=False):
        growth = _pct_growth(prior.eps, current.eps)
        if growth is not None:
            growth_rates.append(growth)

    if not growth_rates:
        return CanslimLetterResult(
            letter="A",
            verdict=CanslimVerdict.INSUFFICIENT_DATA,
            reasons=["Prior-year EPS was never positive in the recent years available"],
        )

    average_growth = sum(growth_rates) / len(growth_rates)
    worst_growth = min(growth_rates)
    years_text = f"{recent[0].period_end} to {recent[-1].period_end}"

    if (
        average_growth >= ANNUAL_GROWTH_THRESHOLD_PCT
        and worst_growth >= ANNUAL_DECLINE_TOLERANCE_PCT
    ):
        verdict = CanslimVerdict.PASS
        reasons = [
            f"Average annual EPS growth {average_growth:.1f}% over {years_text} "
            f"(threshold: {ANNUAL_GROWTH_THRESHOLD_PCT:.0f}%), no year worse than "
            f"{worst_growth:.1f}%"
        ]
    elif average_growth < ANNUAL_GROWTH_THRESHOLD_PCT:
        verdict = CanslimVerdict.FAIL
        reasons = [
            f"Average annual EPS growth {average_growth:.1f}% over {years_text}, below "
            f"the {ANNUAL_GROWTH_THRESHOLD_PCT:.0f}% threshold"
        ]
    else:
        verdict = CanslimVerdict.FAIL
        reasons = [
            f"A down year of {worst_growth:.1f}% over {years_text} is worse than the "
            f"{ANNUAL_DECLINE_TOLERANCE_PCT:.0f}% tolerance, despite "
            f"{average_growth:.1f}% average growth"
        ]

    return CanslimLetterResult(
        letter="A",
        verdict=verdict,
        reasons=reasons,
        values={
            "average_annual_growth_pct": round(average_growth, 2),
            "worst_annual_growth_pct": round(worst_growth, 2),
            "years_used": len(recent),
        },
    )
