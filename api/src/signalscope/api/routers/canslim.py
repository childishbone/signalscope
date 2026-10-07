"""CANSLIM checklist endpoint, covering the whole watchlist at once."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from signalscope.api.schemas import SecurityOut
from signalscope.api.schemas_canslim import (
    CanslimConstituentOut,
    CanslimLetterOut,
    SecurityCanslimOut,
)
from signalscope.db.models import Security, WatchlistItem
from signalscope.db.session import get_db
from signalscope.market_data.yahoo import YahooProvider
from signalscope.services.canslim import BenchmarkCache, CanslimResult, compute_canslim_for_security
from signalscope.signals.canslim_types import CanslimLetterResult

router = APIRouter(prefix="/api/canslim", tags=["canslim"])

_provider = YahooProvider()


def _to_letter_out(result: CanslimLetterResult) -> CanslimLetterOut:
    constituents = (
        [
            CanslimConstituentOut(
                symbol=c.symbol, name=c.name, weight_pct=c.weight_pct, verdict=c.verdict
            )
            for c in result.constituents
        ]
        if result.constituents is not None
        else None
    )
    return CanslimLetterOut(
        letter=result.letter,
        verdict=result.verdict,
        reasons=result.reasons,
        values=result.values,
        constituents=constituents,
    )


def _to_security_out(security: Security, result: CanslimResult) -> SecurityCanslimOut:
    return SecurityCanslimOut(
        security=SecurityOut.model_validate(security),
        letters={letter: _to_letter_out(r) for letter, r in result.letters.items()},
        score_pct=result.score_pct,
        criteria_evaluated=result.criteria_evaluated,
        criteria_total=result.criteria_total,
    )


@router.get("", response_model=list[SecurityCanslimOut])
def get_watchlist_canslim(db: Session = Depends(get_db)) -> list[SecurityCanslimOut]:
    """CANSLIM checklist for every watchlist security.

    Each distinct market's benchmark index is fetched once and reused
    across every security in that market, rather than re-fetched per
    security (see BenchmarkCache).
    """
    stmt = select(WatchlistItem).join(Security).order_by(Security.symbol)
    items = list(db.scalars(stmt))

    benchmark_cache = BenchmarkCache(_provider)

    results: list[SecurityCanslimOut] = []
    for item in items:
        security = item.security
        benchmark_closes, benchmark_symbol = benchmark_cache.closes_for_country(security.country)
        result = compute_canslim_for_security(
            db, security, _provider, benchmark_closes, benchmark_symbol
        )
        results.append(_to_security_out(security, result))

    return results
