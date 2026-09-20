from sqlalchemy import UniqueConstraint

from signalscope.db import models  # noqa: F401  (registers tables on Base.metadata)
from signalscope.db.base import Base


def test_expected_tables_exist() -> None:
    assert set(Base.metadata.tables) == {
        "securities",
        "watchlist_items",
        "daily_bars",
        "indicator_signals",
        "signal_events",
        "notifications",
        "ingestion_runs",
    }


def test_daily_bars_key_is_security_and_date() -> None:
    table = Base.metadata.tables["daily_bars"]
    assert [c.name for c in table.primary_key.columns] == ["security_id", "trade_date"]


def test_signals_are_unique_per_security_indicator_and_day() -> None:
    table = Base.metadata.tables["indicator_signals"]
    unique_sets = {
        tuple(c.name for c in constraint.columns)
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert ("security_id", "timeframe", "indicator", "as_of_date") in unique_sets


def test_notification_is_unique_per_event_and_channel() -> None:
    table = Base.metadata.tables["notifications"]
    unique_sets = {
        tuple(c.name for c in constraint.columns)
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert ("signal_event_id", "channel") in unique_sets
