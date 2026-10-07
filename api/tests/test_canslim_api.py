"""Tests for the /api/canslim endpoint (signalscope.api.routers.canslim).

The watchlist table always contains real production securities too (this
endpoint deliberately returns the whole watchlist), so these tests filter
the response down to the securities they themselves created rather than
asserting on the total response length.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from signalscope.api.main import app
from signalscope.api.routers import canslim as canslim_module
from signalscope.db.models import DailyBar, Security, WatchlistItem
from signalscope.db.session import get_db
from signalscope.market_data.types import Bar, EarningsHistory


def _client_using(db_session: Session) -> TestClient:
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)


def _insert_security(db_session: Session, symbol: str, country: str = "US") -> Security:
    security = Security(
        symbol=symbol,
        exchange_code="NMS",
        exchange_name="NASDAQ",
        country=country,
        currency="USD",
        name=f"{symbol} Inc.",
        asset_type="equity",
        provider_symbol=symbol,
    )
    db_session.add(security)
    db_session.flush()
    return security


def _insert_watchlist_item(db_session: Session, security: Security) -> WatchlistItem:
    item = WatchlistItem(security_id=security.id)
    db_session.add(item)
    db_session.commit()
    return item


def _insert_bars(db_session: Session, security_id: int, count: int = 300) -> None:
    start = date(2025, 1, 1)
    for i in range(count):
        price = Decimal(str(100.0 + i * 0.5))
        db_session.add(
            DailyBar(
                security_id=security_id,
                trade_date=start + timedelta(days=i),
                open=price,
                high=price,
                low=price,
                close=price,
                adj_close=price,
                volume=1000,
            )
        )
    db_session.commit()


def _fake_bar(day_offset: int, price: float) -> Bar:
    return Bar(
        trade_date=date(2025, 1, 1) + timedelta(days=day_offset),
        open=Decimal(str(price)),
        high=Decimal(str(price)),
        low=Decimal(str(price)),
        close=Decimal(str(price)),
        adj_close=Decimal(str(price)),
        volume=1000,
    )


def test_endpoint_returns_200_with_a_list(db_session: Session) -> None:
    client = _client_using(db_session)
    try:
        response = client.get("/api/canslim")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_computes_canslim_for_watchlist_security(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    security = _insert_security(db_session, "ZZCANSLIM")
    _insert_watchlist_item(db_session, security)
    _insert_bars(db_session, security.id)

    benchmark_bars = [_fake_bar(i, 100.0 + i * 0.1) for i in range(300)]
    monkeypatch.setattr(
        canslim_module._provider,
        "get_historical_bars",
        lambda symbol, period="2y": benchmark_bars,
    )
    monkeypatch.setattr(
        canslim_module._provider,
        "get_earnings_history",
        lambda symbol: EarningsHistory(quarterly_eps=[], annual_eps=[]),
    )
    monkeypatch.setattr(canslim_module._provider, "get_top_holdings", lambda symbol, limit=10: [])

    client = _client_using(db_session)
    try:
        response = client.get("/api/canslim")
        assert response.status_code == 200
        body = response.json()
        matching = [row for row in body if row["security"]["symbol"] == "ZZCANSLIM"]
        assert len(matching) == 1
        assert set(matching[0]["letters"].keys()) == {"C", "A", "N", "S", "L", "M"}
        assert matching[0]["criteria_total"] == 6
    finally:
        app.dependency_overrides.pop(get_db, None)
