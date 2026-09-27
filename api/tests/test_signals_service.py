"""Tests for computing signals from stored bars (signalscope.services.signals)."""

import math
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from signalscope.db.models import DailyBar, Security
from signalscope.services.signals import MINIMUM_BARS_REQUIRED, compute_signals_for_security


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


def test_compute_signals_returns_all_five_with_enough_bars(db_session: Session) -> None:
    security_id = _insert_security_with_bars(db_session, num_bars=260)
    result = compute_signals_for_security(db_session, security_id)

    assert result is not None
    assert result.bars_used == 260
    for indicator in (result.dma, result.rsi, result.ichimoku, result.elliott, result.overall):
        assert len(indicator.reasons) > 0


def test_compute_signals_returns_none_with_insufficient_bars(db_session: Session) -> None:
    security_id = _insert_security_with_bars(db_session, num_bars=MINIMUM_BARS_REQUIRED - 1)
    result = compute_signals_for_security(db_session, security_id)
    assert result is None


def test_compute_signals_returns_none_for_unknown_security(db_session: Session) -> None:
    result = compute_signals_for_security(db_session, security_id=999_999)
    assert result is None
