"""Tests for the /api/securities/{id}/bars endpoint."""

from datetime import date, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from signalscope.api.main import app
from signalscope.db.models import DailyBar, Security
from signalscope.db.session import get_db


def _insert_security_with_bars(db_session: Session, num_bars: int) -> int:
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
    db_session.flush()

    start_date = date(2026, 1, 1)
    for i in range(num_bars):
        price = 100 + i
        db_session.add(
            DailyBar(
                security_id=security.id,
                trade_date=start_date + timedelta(days=i),
                open=Decimal(price),
                high=Decimal(price + 1),
                low=Decimal(price - 1),
                close=Decimal(price),
                adj_close=Decimal(price),
                volume=1_000_000,
            )
        )
    db_session.commit()
    return security.id


def _client_using(db_session: Session) -> TestClient:
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)


def test_bars_endpoint_returns_chronological_order(db_session: Session) -> None:
    security_id = _insert_security_with_bars(db_session, num_bars=10)
    client = _client_using(db_session)
    try:
        response = client.get(f"/api/securities/{security_id}/bars")
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 10
        dates = [bar["trade_date"] for bar in body]
        assert dates == sorted(dates)
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_bars_endpoint_respects_limit(db_session: Session) -> None:
    security_id = _insert_security_with_bars(db_session, num_bars=10)
    client = _client_using(db_session)
    try:
        response = client.get(f"/api/securities/{security_id}/bars?limit=3")
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 3
        # Limit keeps the most recent bars, still in chronological order.
        assert body[-1]["trade_date"] == "2026-01-10"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_bars_endpoint_unknown_security_returns_404(db_session: Session) -> None:
    client = _client_using(db_session)
    try:
        response = client.get("/api/securities/999999/bars")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_db, None)
