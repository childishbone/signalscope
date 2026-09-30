"""Recent signal-state-change events, across all watchlist securities."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from signalscope.api.schemas import SecurityOut
from signalscope.api.schemas_signal_events import SignalEventOut
from signalscope.db.models import Security, SignalEvent
from signalscope.db.session import get_db
from signalscope.signals.types import SignalState

router = APIRouter(prefix="/api/signal-events", tags=["signal-events"])


@router.get("", response_model=list[SignalEventOut])
def list_recent_signal_events(
    limit: int = 20, db: Session = Depends(get_db)
) -> list[SignalEventOut]:
    stmt = (
        select(SignalEvent, Security)
        .join(Security, SignalEvent.security_id == Security.id)
        .order_by(SignalEvent.created_at.desc())
        .limit(limit)
    )
    rows = db.execute(stmt).all()
    return [
        SignalEventOut(
            id=event.id,
            security=SecurityOut.model_validate(security),
            indicator=event.indicator,
            from_state=SignalState(event.from_state),
            to_state=SignalState(event.to_state),
            as_of_date=event.as_of_date,
            created_at=event.created_at,
        )
        for event, security in rows
    ]
