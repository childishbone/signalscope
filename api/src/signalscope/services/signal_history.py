"""Persisting computed signals day-by-day, and detecting when a signal's
state changes from what was last recorded.

This is what turns the on-the-fly signals from `services.signals` into a
history: every time signals are (re)computed for a security -- from the
watchlist's manual "Refresh data" action, or the scheduled batch refresh
-- this module writes one `indicator_signals` row per indicator for that
trading day, and if an indicator's state differs from the most recently
recorded prior day, it also writes a `signal_events` row.
"""

from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from signalscope.db.models import IndicatorSignal, SignalEvent
from signalscope.services.signals import SecuritySignals
from signalscope.signals.types import IndicatorResult, SignalState

# Bumping this lets a detail screen distinguish "the rules changed" from
# "the market changed" when looking at historical signals.
RULESET_VERSION = "1.0"
TIMEFRAME = "1D"


@dataclass(frozen=True)
class SignalChange:
    """One indicator's recorded state differs from what was last stored
    for that security, as of a newly-computed trading day."""

    event_id: int
    indicator: str
    from_state: SignalState
    to_state: SignalState


def _previous_state(
    db: Session, security_id: int, indicator: str, before: date
) -> SignalState | None:
    """The most recently recorded state for this indicator, strictly
    before `before`. None if nothing has ever been recorded."""
    stmt = (
        select(IndicatorSignal.state)
        .where(
            IndicatorSignal.security_id == security_id,
            IndicatorSignal.timeframe == TIMEFRAME,
            IndicatorSignal.indicator == indicator,
            IndicatorSignal.as_of_date < before,
        )
        .order_by(IndicatorSignal.as_of_date.desc())
        .limit(1)
    )
    state = db.scalar(stmt)
    return SignalState(state) if state is not None else None


def _upsert_indicator_signal(
    db: Session,
    security_id: int,
    indicator: str,
    as_of_date: date,
    result: IndicatorResult,
) -> None:
    """Write (or overwrite) today's row for this security/indicator. Safe
    to call more than once for the same day -- e.g. clicking "Refresh
    data" twice -- since it upserts rather than inserts."""
    insert_stmt = insert(IndicatorSignal).values(
        security_id=security_id,
        timeframe=TIMEFRAME,
        indicator=indicator,
        as_of_date=as_of_date,
        state=result.state.value,
        score=round(result.score, 2),
        ruleset_version=RULESET_VERSION,
        details={"reasons": result.reasons, "values": result.values},
    )
    upsert_stmt = insert_stmt.on_conflict_do_update(
        index_elements=["security_id", "timeframe", "indicator", "as_of_date"],
        set_={
            "state": insert_stmt.excluded.state,
            "score": insert_stmt.excluded.score,
            "ruleset_version": insert_stmt.excluded.ruleset_version,
            "details": insert_stmt.excluded.details,
            "computed_at": func.now(),
        },
    )
    db.execute(upsert_stmt)


def _record_event_if_changed(
    db: Session,
    security_id: int,
    indicator: str,
    as_of_date: date,
    previous: SignalState | None,
    current: SignalState,
) -> SignalChange | None:
    """Write a `signal_events` row if the state actually changed. Returns
    None if there's no prior state to have changed from, or if this exact
    change was already recorded (e.g. "Refresh data" clicked twice in one
    day) -- in the latter case nothing new happened, so nothing is
    reported, even though the underlying row already exists."""
    if previous is None or previous == current:
        return None

    insert_stmt = insert(SignalEvent).values(
        security_id=security_id,
        timeframe=TIMEFRAME,
        indicator=indicator,
        as_of_date=as_of_date,
        from_state=previous.value,
        to_state=current.value,
    )
    # Re-running the same day's refresh must not double-write the event,
    # and RETURNING tells us whether this call was the one that wrote it.
    returning_stmt = insert_stmt.on_conflict_do_nothing(
        index_elements=["security_id", "timeframe", "indicator", "as_of_date"],
    ).returning(SignalEvent.id)
    inserted = db.execute(returning_stmt).first()
    if inserted is None:
        return None
    return SignalChange(
        event_id=inserted.id, indicator=indicator, from_state=previous, to_state=current
    )


def record_signals(db: Session, security_id: int, signals: SecuritySignals) -> list[SignalChange]:
    """Persist one security's freshly-computed signals and report any
    indicators whose state changed since the last time they were recorded."""
    indicators: dict[str, IndicatorResult] = {
        "dma": signals.dma,
        "rsi": signals.rsi,
        "ichimoku": signals.ichimoku,
        "elliott": signals.elliott,
        "overall": signals.overall,
    }

    changes: list[SignalChange] = []
    for indicator, result in indicators.items():
        previous = _previous_state(db, security_id, indicator, signals.as_of_date)
        _upsert_indicator_signal(db, security_id, indicator, signals.as_of_date, result)
        change = _record_event_if_changed(
            db, security_id, indicator, signals.as_of_date, previous, result.state
        )
        if change is not None:
            changes.append(change)

    db.commit()
    return changes
