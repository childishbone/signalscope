"""Tests for persisting signals and detecting state changes over time
(signalscope.services.signal_history)."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from signalscope.db.models import IndicatorSignal, Security, SignalEvent
from signalscope.services.signal_history import record_signals
from signalscope.services.signals import SecuritySignals
from signalscope.signals.types import IndicatorResult, SignalState


def _insert_security(db_session: Session) -> int:
    security = Security(
        symbol="TEST",
        exchange_code="NMS",
        exchange_name="NASDAQ",
        country="US",
        currency="USD",
        name="Test Security",
        asset_type="equity",
        provider_symbol="TEST",
    )
    db_session.add(security)
    db_session.commit()
    return security.id


def _flat_signals(
    as_of_date: date, *, dma_state: SignalState = SignalState.NEUTRAL
) -> SecuritySignals:
    """All five indicators Neutral except DMA, which is configurable, so
    tests can flip exactly one indicator between calls."""

    def result(state: SignalState) -> IndicatorResult:
        return IndicatorResult(state=state, score=0.0, reasons=["test reason"], values={})

    return SecuritySignals(
        dma=result(dma_state),
        rsi=result(SignalState.NEUTRAL),
        ichimoku=result(SignalState.NEUTRAL),
        elliott=result(SignalState.NEUTRAL),
        overall=result(SignalState.NEUTRAL),
        bars_used=999,
        as_of_date=as_of_date,
    )


def test_first_recording_creates_rows_but_no_events(db_session: Session) -> None:
    security_id = _insert_security(db_session)
    signals = _flat_signals(date(2026, 1, 2))

    changes = record_signals(db_session, security_id, signals)

    assert changes == []
    rows = list(
        db_session.scalars(
            select(IndicatorSignal).where(IndicatorSignal.security_id == security_id)
        )
    )
    assert len(rows) == 5
    assert {row.indicator for row in rows} == {"dma", "rsi", "ichimoku", "elliott", "overall"}
    assert all(row.state == "neutral" for row in rows)


def test_state_change_is_recorded_as_an_event(db_session: Session) -> None:
    security_id = _insert_security(db_session)
    record_signals(db_session, security_id, _flat_signals(date(2026, 1, 2)))

    changes = record_signals(
        db_session, security_id, _flat_signals(date(2026, 1, 3), dma_state=SignalState.BULLISH)
    )

    assert len(changes) == 1
    assert changes[0].indicator == "dma"
    assert changes[0].from_state == SignalState.NEUTRAL
    assert changes[0].to_state == SignalState.BULLISH

    events = list(
        db_session.scalars(select(SignalEvent).where(SignalEvent.security_id == security_id))
    )
    assert len(events) == 1
    assert events[0].indicator == "dma"
    assert events[0].from_state == "neutral"
    assert events[0].to_state == "bullish"


def test_unchanged_indicators_produce_no_events(db_session: Session) -> None:
    security_id = _insert_security(db_session)
    record_signals(db_session, security_id, _flat_signals(date(2026, 1, 2)))

    changes = record_signals(db_session, security_id, _flat_signals(date(2026, 1, 3)))

    assert changes == []


def test_rerunning_the_same_day_does_not_duplicate_events_or_inflate_the_count(
    db_session: Session,
) -> None:
    security_id = _insert_security(db_session)
    record_signals(db_session, security_id, _flat_signals(date(2026, 1, 2)))
    day2 = _flat_signals(date(2026, 1, 3), dma_state=SignalState.BULLISH)

    first_run_changes = record_signals(db_session, security_id, day2)
    second_run_changes = record_signals(db_session, security_id, day2)

    assert len(first_run_changes) == 1
    assert second_run_changes == []

    events = list(
        db_session.scalars(select(SignalEvent).where(SignalEvent.security_id == security_id))
    )
    assert len(events) == 1

    rows = list(
        db_session.scalars(
            select(IndicatorSignal).where(
                IndicatorSignal.security_id == security_id,
                IndicatorSignal.indicator == "dma",
            )
        )
    )
    assert len(rows) == 2  # one row per distinct as_of_date, not per call
