"""Tests for sending and recording Telegram notifications
(signalscope.services.notifications)."""

from datetime import date

import pytest
from sqlalchemy.orm import Session

from signalscope.db.models import Security, SignalEvent
from signalscope.services import notifications as notifications_module
from signalscope.services.notifications import notify_signal_event


def _insert_signal_event(db_session: Session) -> int:
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

    event = SignalEvent(
        security_id=security.id,
        timeframe="1D",
        indicator="dma",
        as_of_date=date(2026, 1, 2),
        from_state="neutral",
        to_state="bullish",
    )
    db_session.add(event)
    db_session.commit()
    return event.id


def test_successful_send_records_sent_status(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    event_id = _insert_signal_event(db_session)
    monkeypatch.setattr(notifications_module, "send_telegram_message", lambda text: None)

    notification = notify_signal_event(
        db_session,
        event_id=event_id,
        security_symbol="TEST",
        indicator="dma",
        from_state="neutral",
        to_state="bullish",
        as_of_date=date(2026, 1, 2),
    )

    assert notification.status == "sent"
    assert notification.error is None
    assert notification.sent_at is not None
    assert notification.attempts == 1


def test_failed_send_records_failed_status(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    event_id = _insert_signal_event(db_session)

    def _raise(text: str) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(notifications_module, "send_telegram_message", _raise)

    notification = notify_signal_event(
        db_session,
        event_id=event_id,
        security_symbol="TEST",
        indicator="dma",
        from_state="neutral",
        to_state="bullish",
        as_of_date=date(2026, 1, 2),
    )

    assert notification.status == "failed"
    assert notification.error == "boom"
    assert notification.sent_at is None


def test_retrying_reuses_the_same_notification_row(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    event_id = _insert_signal_event(db_session)

    def _raise(text: str) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(notifications_module, "send_telegram_message", _raise)
    first = notify_signal_event(
        db_session,
        event_id=event_id,
        security_symbol="TEST",
        indicator="dma",
        from_state="neutral",
        to_state="bullish",
        as_of_date=date(2026, 1, 2),
    )

    monkeypatch.setattr(notifications_module, "send_telegram_message", lambda text: None)
    second = notify_signal_event(
        db_session,
        event_id=event_id,
        security_symbol="TEST",
        indicator="dma",
        from_state="neutral",
        to_state="bullish",
        as_of_date=date(2026, 1, 2),
    )

    assert first.id == second.id
    assert second.status == "sent"
    assert second.attempts == 2
