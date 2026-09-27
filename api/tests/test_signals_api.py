"""Tests for the /api/securities/{id}/signals endpoint."""

import math
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

    start_date = date(2020, 1, 1)
    for i in range(num_bars):
        price = 100 + 0.15 * i + 2 * math.sin(i * 0.3)
        trade_date = start_date + timedelta(days=i)
        db_session.add(
            DailyBar(
                security_id=security.id,
                trade_date=trade_date,
                open=Decimal(str(round(price - 0.05, 4))),
                high=Decimal(str(round(price + 0.3, 4))),
                low=Decimal(str(round(price - 0.3, 4))),
                close=Decimal(str(round(price, 4))),
                adj_close=Decimal(str(round(price, 4))),
                volume=1_000_000,
            )
        )
    db_session.commit()
    return security.id


def _client_using(db_session: Session) -> TestClient:
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)


def test_signals_endpoint_returns_all_five_signals(db_session: Session) -> None:
    security_id = _insert_security_with_bars(db_session, num_bars=260)
    client = _client_using(db_session)
    try:
        response = client.get(f"/api/securities/{security_id}/signals")
        assert response.status_code == 200
        body = response.json()
        assert body["bars_used"] == 260
        for key in ("dma", "rsi", "ichimoku", "elliott", "overall"):
            assert key in body
            assert body[key]["state"] in ("bullish", "neutral", "bearish")
            assert len(body[key]["reasons"]) > 0
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_signals_endpoint_with_insufficient_bars_returns_422(db_session: Session) -> None:
    security_id = _insert_security_with_bars(db_session, num_bars=50)
    client = _client_using(db_session)
    try:
        response = client.get(f"/api/securities/{security_id}/signals")
        assert response.status_code == 422
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_signals_endpoint_unknown_security_returns_404(db_session: Session) -> None:
    client = _client_using(db_session)
    try:
        response = client.get("/api/securities/999999/signals")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_db, None)
