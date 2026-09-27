"""Fetching and storing daily OHLCV bars."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from signalscope.db.models import DailyBar, Security
from signalscope.market_data.base import MarketDataProvider


@dataclass(frozen=True)
class QuoteSnapshot:
    """Everything the Watchlist UI needs, computed from stored bars."""

    latest_price: Decimal
    latest_date: date
    change: Decimal
    change_pct: Decimal
    volume: int
    high_52w: Decimal
    low_52w: Decimal


def refresh_bars(db: Session, security: Security, provider: MarketDataProvider) -> int:
    """Fetch ~2y of daily bars and upsert them. Returns the number of bars written."""
    bars = provider.get_historical_bars(security.provider_symbol, period="2y")
    if not bars:
        return 0

    rows = [
        {
            "security_id": security.id,
            "trade_date": bar.trade_date,
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "adj_close": bar.adj_close,
            "volume": bar.volume,
        }
        for bar in bars
    ]

    # One statement, upserting all rows: re-running this never creates duplicates,
    # and it corrects any bar Yahoo later fills in (see Phase 0's ETF NaN finding).
    stmt = insert(DailyBar).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["security_id", "trade_date"],
        set_={
            "open": stmt.excluded.open,
            "high": stmt.excluded.high,
            "low": stmt.excluded.low,
            "close": stmt.excluded.close,
            "adj_close": stmt.excluded.adj_close,
            "volume": stmt.excluded.volume,
        },
    )
    db.execute(stmt)
    db.commit()
    return len(rows)


def compute_snapshot(db: Session, security_id: int) -> QuoteSnapshot | None:
    """Derive latest price, change, and 52-week range from stored bars alone."""
    stmt = (
        select(DailyBar)
        .where(DailyBar.security_id == security_id)
        .order_by(DailyBar.trade_date.desc())
        .limit(260)  # slightly over a year of trading days, enough for a 52w range
    )
    bars = list(db.scalars(stmt))
    if not bars:
        return None

    latest = bars[0]
    previous = bars[1] if len(bars) > 1 else None

    change = latest.close - previous.close if previous else Decimal("0")
    change_pct = (change / previous.close * 100) if previous and previous.close else Decimal("0")

    return QuoteSnapshot(
        latest_price=latest.close,
        latest_date=latest.trade_date,
        change=change,
        change_pct=change_pct,
        volume=latest.volume,
        high_52w=max(b.high for b in bars),
        low_52w=min(b.low for b in bars),
    )
