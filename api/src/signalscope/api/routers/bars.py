"""Historical daily price bars, for charting."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from signalscope.api.schemas_bars import DailyBarOut
from signalscope.db.models import DailyBar, Security
from signalscope.db.session import get_db

router = APIRouter(prefix="/api/securities", tags=["bars"])

DEFAULT_LIMIT = 180
MAX_LIMIT = 600  # covers a full ~2y of trading days, the most history we store


@router.get("/{security_id}/bars", response_model=list[DailyBarOut])
def get_daily_bars(
    security_id: int, limit: int = DEFAULT_LIMIT, db: Session = Depends(get_db)
) -> list[DailyBarOut]:
    security = db.get(Security, security_id)
    if security is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Security not found")

    limit = min(limit, MAX_LIMIT)
    stmt = (
        select(DailyBar)
        .where(DailyBar.security_id == security_id)
        .order_by(DailyBar.trade_date.desc())
        .limit(limit)
    )
    bars = list(db.scalars(stmt))
    bars.reverse()  # chronological order, oldest first, for charting

    return [
        DailyBarOut(
            trade_date=bar.trade_date,
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            volume=bar.volume,
        )
        for bar in bars
    ]
