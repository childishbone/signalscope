"""Database tables."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from signalscope.db.base import Base

_STATES = "('bullish', 'neutral', 'bearish')"
_INDICATORS = "('dma', 'rsi', 'ichimoku', 'elliott', 'overall')"


class Security(Base):
    __tablename__ = "securities"
    __table_args__ = (
        UniqueConstraint("exchange_code", "symbol", name="uq_securities_exchange_symbol"),
        CheckConstraint("asset_type in ('equity', 'etf')", name="asset_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str]  # native ticker, e.g. "7203"
    exchange_code: Mapped[str] = mapped_column(String(10))  # ISO 10383 MIC, e.g. "XTKS"
    exchange_name: Mapped[str]  # display name, e.g. "Tokyo Stock Exchange"
    country: Mapped[str] = mapped_column(String(2))  # ISO 3166 alpha-2, e.g. "JP"
    currency: Mapped[str] = mapped_column(String(3))  # e.g. "JPY"
    name: Mapped[str]
    asset_type: Mapped[str] = mapped_column(server_default="equity")
    provider_symbol: Mapped[str] = mapped_column(unique=True)  # symbol for the primary provider
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    # unique = a security appears once. Multiple watchlists would add a watchlist_id later.
    security_id: Mapped[int] = mapped_column(
        ForeignKey("securities.id", ondelete="CASCADE"), unique=True
    )
    added_at: Mapped[datetime] = mapped_column(server_default=func.now())


class DailyBar(Base):
    __tablename__ = "daily_bars"

    security_id: Mapped[int] = mapped_column(
        ForeignKey("securities.id", ondelete="CASCADE"), primary_key=True
    )
    trade_date: Mapped[date] = mapped_column(primary_key=True)  # exchange-local trading day
    open: Mapped[Decimal]
    high: Mapped[Decimal]
    low: Mapped[Decimal]
    close: Mapped[Decimal]
    adj_close: Mapped[Decimal | None]
    volume: Mapped[int] = mapped_column(BigInteger)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class IndicatorSignal(Base):
    __tablename__ = "indicator_signals"
    __table_args__ = (
        UniqueConstraint(
            "security_id",
            "timeframe",
            "indicator",
            "as_of_date",
            name="uq_indicator_signals_key",
        ),
        CheckConstraint(f"state in {_STATES}", name="state"),
        CheckConstraint(f"indicator in {_INDICATORS}", name="indicator"),
        CheckConstraint("score between -2 and 2", name="score_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    security_id: Mapped[int] = mapped_column(ForeignKey("securities.id", ondelete="CASCADE"))
    timeframe: Mapped[str] = mapped_column(String(8), server_default="1D")
    indicator: Mapped[str] = mapped_column(String(16))
    as_of_date: Mapped[date]  # trading day of the last bar analysed
    state: Mapped[str] = mapped_column(String(8))
    # Model scores are whole numbers (-2..+2); "overall" can be a weighted average.
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    ruleset_version: Mapped[str] = mapped_column(String(16))
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    computed_at: Mapped[datetime] = mapped_column(server_default=func.now())


class SignalEvent(Base):
    __tablename__ = "signal_events"
    __table_args__ = (
        UniqueConstraint(
            "security_id",
            "timeframe",
            "indicator",
            "as_of_date",
            name="uq_signal_events_key",
        ),
        CheckConstraint(f"from_state in {_STATES}", name="from_state"),
        CheckConstraint(f"to_state in {_STATES}", name="to_state"),
        CheckConstraint("from_state <> to_state", name="state_changed"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    security_id: Mapped[int] = mapped_column(ForeignKey("securities.id", ondelete="CASCADE"))
    timeframe: Mapped[str] = mapped_column(String(8), server_default="1D")
    indicator: Mapped[str] = mapped_column(String(16))
    as_of_date: Mapped[date]
    from_state: Mapped[str] = mapped_column(String(8))
    to_state: Mapped[str] = mapped_column(String(8))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint("signal_event_id", "channel", name="uq_notifications_event_channel"),
        CheckConstraint("status in ('pending', 'sent', 'failed')", name="status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    signal_event_id: Mapped[int] = mapped_column(ForeignKey("signal_events.id", ondelete="CASCADE"))
    channel: Mapped[str] = mapped_column(String(16), server_default="telegram")
    status: Mapped[str] = mapped_column(String(16), server_default="pending")
    message: Mapped[str] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(server_default="0")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    sent_at: Mapped[datetime | None]


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    __table_args__ = (
        CheckConstraint("status in ('running', 'succeeded', 'partial', 'failed')", name="status"),
        CheckConstraint("triggered_by in ('schedule', 'manual')", name="triggered_by"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    triggered_by: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), server_default="running")
    started_at: Mapped[datetime] = mapped_column(server_default=func.now())
    finished_at: Mapped[datetime | None]
    securities_total: Mapped[int] = mapped_column(server_default="0")
    securities_failed: Mapped[int] = mapped_column(server_default="0")
    bars_upserted: Mapped[int] = mapped_column(server_default="0")
    error_summary: Mapped[str | None] = mapped_column(Text)
