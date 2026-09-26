import os

import pytest
from fastapi.testclient import TestClient

from signalscope.api.main import app

pytestmark = pytest.mark.skipif(
    os.environ.get("SIGNALSCOPE_NETWORK_TESTS") != "1",
    reason="Search calls the real Yahoo API; set SIGNALSCOPE_NETWORK_TESTS=1",
)


def test_search_returns_json_matches() -> None:
    with TestClient(app) as client:
        response = client.get("/api/securities/search", params={"q": "Toyota"})
    assert response.status_code == 200
    results = response.json()
    assert any(r["provider_symbol"] == "7203.T" for r in results)


def test_empty_query_returns_empty_list() -> None:
    with TestClient(app) as client:
        response = client.get("/api/securities/search", params={"q": "  "})
    assert response.status_code == 200
    assert response.json() == []
