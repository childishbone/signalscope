import os

import pytest
from fastapi.testclient import TestClient

from signalscope.api.deps import require_admin
from signalscope.api.main import app
from signalscope.db.session import get_db

pytestmark = pytest.mark.skipif(
    os.environ.get("SIGNALSCOPE_NETWORK_TESTS") != "1",
    reason="Adding a new security calls the real Yahoo search; set SIGNALSCOPE_NETWORK_TESTS=1",
)

AAPL_PAYLOAD = {"provider_symbol": "AAPL"}


@pytest.fixture()
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[require_admin] = lambda: None
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_add_list_and_remove_watchlist_item(client: TestClient) -> None:
    response = client.post("/api/watchlist", json=AAPL_PAYLOAD)
    assert response.status_code == 201
    item = response.json()
    assert item["security"]["symbol"] == "AAPL"

    listing = client.get("/api/watchlist").json()
    assert any(row["id"] == item["id"] for row in listing)

    delete_response = client.delete(f"/api/watchlist/{item['id']}")
    assert delete_response.status_code == 204


def test_adding_same_security_twice_is_rejected(client: TestClient) -> None:
    client.post("/api/watchlist", json=AAPL_PAYLOAD)
    second = client.post("/api/watchlist", json=AAPL_PAYLOAD)
    assert second.status_code == 409


def test_adding_unknown_symbol_returns_404(client: TestClient) -> None:
    response = client.post("/api/watchlist", json={"provider_symbol": "NOTREALXYZ"})
    assert response.status_code == 404


def test_write_endpoints_require_admin_key() -> None:
    app.dependency_overrides[get_db] = lambda: None
    try:
        with TestClient(app) as test_client:
            response = test_client.post("/api/watchlist", json=AAPL_PAYLOAD)
    finally:
        app.dependency_overrides.clear()
    assert response.status_code in (401, 503)
