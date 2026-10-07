"""Computing all six CANSLIM letters for one security.

N, S, M, and L are purely technical (price/volume, already stored as
DailyBar rows). C and A need earnings data, which a plain ETF/fund simply
doesn't have -- for those, a qualifying fund (one with enough real,
identifiable constituent holdings) has C and A computed per top holding
and combined with a weight-adjusted pass rate; a fund without usable
holdings data (e.g. a leveraged/derivative-based fund) resolves to
Insufficient Data instead of a guess.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from signalscope.db.models import DailyBar, Security
from signalscope.market_data.base import MarketDataProvider
from signalscope.market_data.types import EarningsHistory, FundHolding
from signalscope.signals.canslim_earnings import (
    score_annual_earnings_growth,
    score_current_earnings_growth,
)
from signalscope.signals.canslim_market_direction import score_market_direction
from signalscope.signals.canslim_new_high import score_new_high
from signalscope.signals.canslim_relative_strength import score_relative_strength
from signalscope.signals.canslim_supply_demand import score_supply_demand
from signalscope.signals.canslim_types import (
    CanslimConstituentResult,
    CanslimLetterResult,
    CanslimVerdict,
)

ALL_LETTERS = ("C", "A", "N", "S", "L", "M")

TOP_HOLDINGS_COUNT = 5
MINIMUM_HOLDINGS_REQUIRED = 3  # fewer than this means no real basket to analyze (e.g. KORU)
FUND_WEIGHTED_PASS_THRESHOLD = 0.5  # majority of evaluated weight must pass


@dataclass(frozen=True)
class CanslimResult:
    """All six letters for one security, plus a score computed only from
    the letters that could actually be evaluated."""

    letters: dict[str, CanslimLetterResult]
    score_pct: float | None  # None if nothing at all could be evaluated
    criteria_evaluated: int
    criteria_total: int


def _load_closes_and_volumes(db: Session, security_id: int) -> tuple[list[float], list[int]]:
    stmt = (
        select(DailyBar)
        .where(DailyBar.security_id == security_id)
        .order_by(DailyBar.trade_date.asc())
    )
    bars = list(db.scalars(stmt))
    return [float(bar.close) for bar in bars], [bar.volume for bar in bars]


def _score_fund_letter(
    letter: str,
    holdings: list[FundHolding],
    provider: MarketDataProvider,
    score_one: Callable[[EarningsHistory], CanslimLetterResult],
) -> CanslimLetterResult:
    """Score one earnings letter (C or A) for a fund by aggregating across
    its top holdings, weighted by each holding's share of the fund."""
    constituents: list[CanslimConstituentResult] = []
    for holding in holdings:
        earnings = provider.get_earnings_history(holding.symbol)
        result = score_one(earnings)
        constituents.append(
            CanslimConstituentResult(
                symbol=holding.symbol,
                name=holding.name,
                weight_pct=holding.weight_pct,
                verdict=result.verdict,
            )
        )

    coverage_pct = sum(c.weight_pct for c in constituents)
    evaluated = [c for c in constituents if c.verdict != CanslimVerdict.INSUFFICIENT_DATA]
    evaluated_weight = sum(c.weight_pct for c in evaluated)

    if evaluated_weight == 0:
        return CanslimLetterResult(
            letter=letter,
            verdict=CanslimVerdict.INSUFFICIENT_DATA,
            reasons=["None of the fund's top holdings had usable earnings data"],
            constituents=constituents,
        )

    pass_weight = sum(c.weight_pct for c in evaluated if c.verdict == CanslimVerdict.PASS)
    weighted_pass_ratio = pass_weight / evaluated_weight
    verdict = (
        CanslimVerdict.PASS
        if weighted_pass_ratio >= FUND_WEIGHTED_PASS_THRESHOLD
        else CanslimVerdict.FAIL
    )

    return CanslimLetterResult(
        letter=letter,
        verdict=verdict,
        reasons=[
            f"Top {len(holdings)} holdings cover {coverage_pct:.1f}% of the fund; "
            f"{weighted_pass_ratio * 100:.0f}% of evaluated weight passes letter {letter}"
        ],
        values={
            "coverage_pct": round(coverage_pct, 2),
            "weighted_pass_ratio": round(weighted_pass_ratio, 4),
        },
        constituents=constituents,
    )


def _score_earnings_letters(
    security: Security, provider: MarketDataProvider
) -> tuple[CanslimLetterResult, CanslimLetterResult]:
    if security.asset_type != "etf":
        earnings = provider.get_earnings_history(security.provider_symbol)
        return (
            score_current_earnings_growth(earnings.quarterly_eps),
            score_annual_earnings_growth(earnings.annual_eps),
        )

    holdings = provider.get_top_holdings(security.provider_symbol, limit=TOP_HOLDINGS_COUNT)
    if len(holdings) < MINIMUM_HOLDINGS_REQUIRED:
        reasons = [
            "Fund holdings data unavailable or too sparse to analyze (found "
            f"{len(holdings)}, need at least {MINIMUM_HOLDINGS_REQUIRED} real "
            "constituent companies) -- likely a leveraged or derivative-based fund"
        ]
        return (
            CanslimLetterResult(
                letter="C", verdict=CanslimVerdict.INSUFFICIENT_DATA, reasons=reasons
            ),
            CanslimLetterResult(
                letter="A", verdict=CanslimVerdict.INSUFFICIENT_DATA, reasons=reasons
            ),
        )

    return (
        _score_fund_letter(
            "C", holdings, provider, lambda eh: score_current_earnings_growth(eh.quarterly_eps)
        ),
        _score_fund_letter(
            "A", holdings, provider, lambda eh: score_annual_earnings_growth(eh.annual_eps)
        ),
    )


def compute_canslim_for_security(
    db: Session,
    security: Security,
    provider: MarketDataProvider,
    benchmark_closes: list[float],
    benchmark_symbol: str | None,
) -> CanslimResult:
    """Compute all six CANSLIM letters for one security.

    `benchmark_closes`/`benchmark_symbol` are passed in rather than
    fetched here, so a caller computing this for an entire watchlist can
    fetch each market's benchmark index once and reuse it across every
    security in that market. `benchmark_symbol=None` means this security's
    market has no configured benchmark -- M and L resolve to Insufficient
    Data rather than erroring.
    """
    closes, volumes = _load_closes_and_volumes(db, security.id)

    letters: dict[str, CanslimLetterResult] = {
        "N": score_new_high(closes),
        "S": score_supply_demand(closes, volumes),
    }

    if benchmark_symbol is None:
        no_benchmark_reason = [f"No benchmark index configured for market '{security.country}'"]
        letters["M"] = CanslimLetterResult(
            letter="M", verdict=CanslimVerdict.INSUFFICIENT_DATA, reasons=no_benchmark_reason
        )
        letters["L"] = CanslimLetterResult(
            letter="L", verdict=CanslimVerdict.INSUFFICIENT_DATA, reasons=no_benchmark_reason
        )
    else:
        letters["M"] = score_market_direction(benchmark_closes, benchmark_symbol)
        letters["L"] = score_relative_strength(closes, benchmark_closes, benchmark_symbol)

    letters["C"], letters["A"] = _score_earnings_letters(security, provider)

    evaluated = [r for r in letters.values() if r.verdict != CanslimVerdict.INSUFFICIENT_DATA]
    if evaluated:
        passed = sum(1 for r in evaluated if r.verdict == CanslimVerdict.PASS)
        score_pct: float | None = round(passed / len(evaluated) * 100, 1)
    else:
        score_pct = None

    return CanslimResult(
        letters=letters,
        score_pct=score_pct,
        criteria_evaluated=len(evaluated),
        criteria_total=len(ALL_LETTERS),
    )
