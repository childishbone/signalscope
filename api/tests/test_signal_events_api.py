"""Tests for the /api/signal-events endpoint."""

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from signalscope.api.main import app
from signalscope.db.models import Security
from signalscope.db.session import get_db
from signalscope.services.signal_history import record_signals
from signalscope.services.signals import SecuritySignals
from signalscope.signals.types import IndicatorResult, SignalState


def _insert_security(db_session: Session, symbol: str) -> int:
    security = Security(
        symbol=symbol,
        exchange_code="NMS",
        exchange_name="NASDAQ",
        country="US",
        currency="USD",
        name=f"{symbol} Inc.",
        asset_type="equity",
        provider_symbol=symbol,
    )
    db_session.add(security)
    db_session.commit()
    return security.id


def _flat_signals(
    as_of_date: date, *, dma_state: SignalState = SignalState.NEUTRAL
) -> SecuritySignals:
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


def _client_using(db_session: Session) -> TestClient:
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)


def test_signal_events_endpoint_returns_recent_changes(db_session: Session) -> None:
    security_id = _insert_security(db_session, "AAA")
    record_signals(db_session, security_id, _flat_signals(date(2026, 1, 2)))
    record_signals(
        db_session, security_id, _flat_signals(date(2026, 1, 3), dma_state=SignalState.BULLISH)
    )

    client = _client_using(db_session)
    try:
        response = client.get("/api/signal-events")
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        event = body[0]
        assert event["security"]["symbol"] == "AAA"
        assert event["indicator"] == "dma"
        assert event["from_state"] == "neutral"
        assert event["to_state"] == "bullish"
        assert event["as_of_date"] == "2026-01-03"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_signal_events_endpoint_respects_limit(db_session: Session) -> None:
    security_id = _insert_security(db_session, "BBB")
    record_signals(db_session, security_id, _flat_signals(date(2026, 1, 2)))
    record_signals(
        db_session, security_id, _flat_signals(date(2026, 1, 3), dma_state=SignalState.BULLISH)
    )
    record_signals(
        db_session, security_id, _flat_signals(date(2026, 1, 4), dma_state=SignalState.BEARISH)
    )
    record_signals(
        db_session, security_id, _flat_signals(date(2026, 1, 5), dma_state=SignalState.BULLISH)
    )

    client = _client_using(db_session)
    try:
        response = client.get("/api/signal-events?limit=2")
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 2
    finally:
        app.dependency_overrides.pop(get_db, None)
