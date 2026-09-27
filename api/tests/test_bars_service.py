import os
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select

from signalscope.db.models import DailyBar, Security
from signalscope.market_data.types import Bar
from signalscope.services.bars import compute_snapshot, refresh_bars

pytestmark = pytest.mark.skipif(
    os.environ.get("SIGNALSCOPE_NETWORK_TESTS") != "1",
    reason="refresh_bars calls the real Yahoo API; set SIGNALSCOPE_NETWORK_TESTS=1",
)


class _FakeProvider:
    """Avoids depending on Yahoo's real data shape for a pure logic test."""

    def __init__(self, bars: list[Bar]) -> None:
        self._bars = bars

    def search_securities(self, query: str, limit: int = 8) -> list:
        raise NotImplementedError

    def get_historical_bars(self, provider_symbol: str, period: str = "2y") -> list[Bar]:
        return self._bars


def _make_security(db_session) -> Security:
    security = Security(
        symbol="TEST",
        exchange_code="XNAS",
        exchange_name="NASDAQ",
        country="US",
        currency="USD",
        name="Test Security",
        asset_type="equity",
        provider_symbol="TESTBARS",
    )
    db_session.add(security)
    db_session.flush()
    return security


def test_refresh_bars_writes_expected_row_count(db_session) -> None:
    security = _make_security(db_session)
    bars = [
        Bar(
            date(2026, 1, 2),
            Decimal("100"),
            Decimal("105"),
            Decimal("99"),
            Decimal("104"),
            None,
            1000,
        ),
        Bar(
            date(2026, 1, 3),
            Decimal("104"),
            Decimal("110"),
            Decimal("103"),
            Decimal("108"),
            None,
            1200,
        ),
    ]
    written = refresh_bars(db_session, security, _FakeProvider(bars))
    assert written == 2

    stored = list(db_session.scalars(select(DailyBar).where(DailyBar.security_id == security.id)))
    assert len(stored) == 2


def test_refresh_bars_upserts_without_duplicating(db_session) -> None:
    security = _make_security(db_session)
    original = [
        Bar(
            date(2026, 1, 2),
            Decimal("100"),
            Decimal("105"),
            Decimal("99"),
            Decimal("104"),
            None,
            1000,
        ),
    ]
    refresh_bars(db_session, security, _FakeProvider(original))

    corrected = [
        Bar(
            date(2026, 1, 2),
            Decimal("100"),
            Decimal("105"),
            Decimal("99"),
            Decimal("106"),
            None,
            1000,
        ),
    ]
    refresh_bars(db_session, security, _FakeProvider(corrected))

    stored = list(db_session.scalars(select(DailyBar).where(DailyBar.security_id == security.id)))
    assert len(stored) == 1
    assert stored[0].close == Decimal("106")


def test_compute_snapshot_returns_none_with_no_bars(db_session) -> None:
    security = _make_security(db_session)
    assert compute_snapshot(db_session, security.id) is None


def test_compute_snapshot_calculates_change_and_range(db_session) -> None:
    security = _make_security(db_session)
    bars = [
        Bar(
            date(2026, 1, 2),
            Decimal("100"),
            Decimal("105"),
            Decimal("95"),
            Decimal("100"),
            None,
            1000,
        ),
        Bar(
            date(2026, 1, 3),
            Decimal("100"),
            Decimal("112"),
            Decimal("98"),
            Decimal("110"),
            None,
            1200,
        ),
    ]
    refresh_bars(db_session, security, _FakeProvider(bars))

    snapshot = compute_snapshot(db_session, security.id)
    assert snapshot is not None
    assert snapshot.latest_price == Decimal("110")
    assert snapshot.change == Decimal("10")
    assert snapshot.high_52w == Decimal("112")
    assert snapshot.low_52w == Decimal("95")
