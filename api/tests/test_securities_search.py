from fastapi.testclient import TestClient

from signalscope.api.main import app
from signalscope.api.routers import securities as securities_module
from signalscope.market_data.types import SecurityMatch

TOYOTA_MATCH = SecurityMatch(
    symbol="7203",
    provider_symbol="7203.T",
    name="TOYOTA MOTOR CORP",
    exchange_code="XJPX",
    exchange_name="Tokyo Stock Exchange",
    country="JP",
    currency="JPY",
    asset_type="equity",
)


def _fake_search(query: str, limit: int = 8) -> list[SecurityMatch]:
    return [TOYOTA_MATCH] if "toyota" in query.lower() else []


def test_search_returns_json_matches(monkeypatch) -> None:
    monkeypatch.setattr(securities_module._provider, "search_securities", _fake_search)
    with TestClient(app) as client:
        response = client.get("/api/securities/search", params={"q": "Toyota"})
    assert response.status_code == 200
    results = response.json()
    assert any(r["provider_symbol"] == "7203.T" for r in results)


def test_empty_query_returns_empty_list(monkeypatch) -> None:
    monkeypatch.setattr(securities_module._provider, "search_securities", _fake_search)
    with TestClient(app) as client:
        response = client.get("/api/securities/search", params={"q": "  "})
    assert response.status_code == 200
    assert response.json() == []


def test_no_match_returns_empty_list(monkeypatch) -> None:
    monkeypatch.setattr(securities_module._provider, "search_securities", _fake_search)
    with TestClient(app) as client:
        response = client.get("/api/securities/search", params={"q": "nonexistentxyz"})
    assert response.status_code == 200
    assert response.json() == []
