from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from signalscope.api.deps import require_admin
from signalscope.api.main import app
from signalscope.api.routers import watchlist as watchlist_module
from signalscope.db.session import get_db
from signalscope.market_data.types import Bar, SecurityMatch

TEST_PAYLOAD = {"provider_symbol": "ZZTEST"}

TEST_MATCH = SecurityMatch(
    symbol="ZZTEST",
    provider_symbol="ZZTEST",
    name="Test Company",
    exchange_code="XNAS",
    exchange_name="NASDAQ",
    country="US",
    currency="USD",
    asset_type="equity",
)

FAKE_BARS = [
    Bar(
        trade_date=date(2026, 1, 2),
        open=Decimal("100"),
        high=Decimal("105"),
        low=Decimal("99"),
        close=Decimal("104"),
        adj_close=Decimal("104"),
        volume=1_000_000,
    ),
    Bar(
        trade_date=date(2026, 1, 3),
        open=Decimal("104"),
        high=Decimal("108"),
        low=Decimal("103"),
        close=Decimal("107"),
        adj_close=Decimal("107"),
        volume=1_200_000,
    ),
]


def _fake_search(query: str, limit: int = 8) -> list[SecurityMatch]:
    return [TEST_MATCH] if query == "ZZTEST" else []


def _fake_bars(provider_symbol: str, period: str = "2y") -> list[Bar]:
    return FAKE_BARS


@pytest.fixture()
def client(db_session, monkeypatch):
    # No real network calls: swap the real Yahoo provider's methods for fakes,
    # same pattern test_notifications_service.py uses for send_telegram_message.
    monkeypatch.setattr(watchlist_module._provider, "search_securities", _fake_search)
    monkeypatch.setattr(watchlist_module._provider, "get_historical_bars", _fake_bars)
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[require_admin] = lambda: None
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_add_list_and_remove_watchlist_item(client: TestClient) -> None:
    response = client.post("/api/watchlist", json=TEST_PAYLOAD)
    assert response.status_code == 201
    item = response.json()
    assert item["security"]["symbol"] == "ZZTEST"

    listing = client.get("/api/watchlist").json()
    assert any(row["id"] == item["id"] for row in listing)

    delete_response = client.delete(f"/api/watchlist/{item['id']}")
    assert delete_response.status_code == 204


def test_adding_same_security_twice_is_rejected(client: TestClient) -> None:
    client.post("/api/watchlist", json=TEST_PAYLOAD)
    second = client.post("/api/watchlist", json=TEST_PAYLOAD)
    assert second.status_code == 409


def test_adding_unknown_symbol_returns_404(client: TestClient) -> None:
    response = client.post("/api/watchlist", json={"provider_symbol": "NOTREALXYZ"})
    assert response.status_code == 404


def test_refresh_watchlist_item_writes_bars_and_returns_counts(client: TestClient) -> None:
    added = client.post("/api/watchlist", json=TEST_PAYLOAD).json()

    response = client.post(f"/api/watchlist/{added['id']}/refresh")
    assert response.status_code == 200
    body = response.json()
    assert body["bars_written"] == len(FAKE_BARS)
    assert body["signal_changes"] >= 0


def test_refresh_unknown_item_returns_404(client: TestClient) -> None:
    response = client.post("/api/watchlist/999999/refresh")
    assert response.status_code == 404


def test_remove_unknown_item_returns_404(client: TestClient) -> None:
    response = client.delete("/api/watchlist/999999")
    assert response.status_code == 404


def test_write_endpoints_require_admin_key() -> None:
    app.dependency_overrides[get_db] = lambda: None
    try:
        with TestClient(app) as test_client:
            response = test_client.post("/api/watchlist", json=TEST_PAYLOAD)
    finally:
        app.dependency_overrides.clear()
    assert response.status_code in (401, 503)
