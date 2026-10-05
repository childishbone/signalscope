"""Sending Telegram notifications for signal-state changes, and recording
what was sent (or attempted) in the `notifications` table.

Uses the stdlib's `urllib` rather than adding a new HTTP dependency --
Telegram's Bot API is a plain HTTPS POST, and this project already keeps
its dependency list intentionally small.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from signalscope.config import get_settings
from signalscope.db.models import Notification

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"

DISCLAIMER = (
    "Technical signals are generated algorithmically for informational "
    "purposes and do not constitute investment advice."
)


def format_message(
    security_symbol: str,
    security_name: str,
    indicator: str,
    from_state: str,
    to_state: str,
    as_of_date: object,
) -> str:
    return (
        f"SignalScope: {security_name} ({security_symbol})\n"
        f"{indicator.upper()} changed {from_state} -> {to_state} (as of {as_of_date})\n\n"
        f"{DISCLAIMER}"
    )


def send_telegram_message(text: str) -> None:
    """Post a message to the configured Telegram chat. Raises on any
    failure -- the caller is expected to catch it and record the error."""
    settings = get_settings()
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must both be set")

    url = TELEGRAM_API_URL.format(token=settings.telegram_bot_token)
    payload = json.dumps({"chat_id": settings.telegram_chat_id, "text": text}).encode()
    request = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        if response.status != 200:
            raise RuntimeError(f"Telegram API returned status {response.status}")


def notify_signal_event(
    db: Session,
    *,
    event_id: int,
    security_symbol: str,
    security_name: str,
    indicator: str,
    from_state: str,
    to_state: str,
    as_of_date: object,
) -> Notification:
    """Send a Telegram notification for one signal-change event and record
    the attempt. Safe to call more than once for the same event: the
    unique (signal_event_id, channel) row is reused rather than
    duplicated, so a retry just updates the existing record."""
    message = format_message(
        security_symbol, security_name, indicator, from_state, to_state, as_of_date
    )

    notification = db.scalar(
        select(Notification).where(
            Notification.signal_event_id == event_id, Notification.channel == "telegram"
        )
    )
    if notification is None:
        notification = Notification(
            signal_event_id=event_id, channel="telegram", message=message, attempts=0
        )
        db.add(notification)

    notification.message = message
    notification.attempts += 1

    try:
        send_telegram_message(message)
    except Exception as exc:
        notification.status = "failed"
        notification.error = str(exc)
    else:
        notification.status = "sent"
        notification.error = None
        notification.sent_at = datetime.now(UTC)

    db.commit()
    return notification
