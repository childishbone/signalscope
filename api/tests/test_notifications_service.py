"""Tests for sending and recording Telegram notifications
(signalscope.services.notifications)."""

import json
import urllib.request
from datetime import date
from types import SimpleNamespace

import pytest
from sqlalchemy.orm import Session

from signalscope.db.models import Security, SignalEvent
from signalscope.services import notifications as notifications_module
from signalscope.services.notifications import notify_signal_event, send_telegram_message


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


class _FakeResponse:
    """Minimal stand-in for the context manager urllib.request.urlopen returns."""

    def __init__(self, status: int) -> None:
        self.status = status

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *exc_info: object) -> bool:
        return False


def test_send_telegram_message_raises_without_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        notifications_module,
        "get_settings",
        lambda: SimpleNamespace(telegram_bot_token="", telegram_chat_id=""),
    )
    with pytest.raises(RuntimeError, match="TELEGRAM_BOT_TOKEN"):
        send_telegram_message("hello")


def test_send_telegram_message_posts_expected_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        notifications_module,
        "get_settings",
        lambda: SimpleNamespace(telegram_bot_token="FAKETOKEN", telegram_chat_id="12345"),
    )

    captured: dict[str, object] = {}

    def _fake_urlopen(request: urllib.request.Request, timeout: int = 10) -> _FakeResponse:
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode())
        return _FakeResponse(200)

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)

    send_telegram_message("hello world")

    assert captured["url"] == "https://api.telegram.org/botFAKETOKEN/sendMessage"
    assert captured["body"] == {"chat_id": "12345", "text": "hello world"}


def test_send_telegram_message_raises_on_non_200(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        notifications_module,
        "get_settings",
        lambda: SimpleNamespace(telegram_bot_token="FAKETOKEN", telegram_chat_id="12345"),
    )
    monkeypatch.setattr(urllib.request, "urlopen", lambda request, timeout=10: _FakeResponse(500))

    with pytest.raises(RuntimeError, match="status 500"):
        send_telegram_message("hello")
