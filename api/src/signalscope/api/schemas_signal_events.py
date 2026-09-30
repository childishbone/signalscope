"""Response schema for the recent-signal-events endpoint."""

from datetime import date, datetime

from pydantic import BaseModel

from signalscope.api.schemas import SecurityOut
from signalscope.signals.types import SignalState


class SignalEventOut(BaseModel):
    id: int
    security: SecurityOut
    indicator: str
    from_state: SignalState
    to_state: SignalState
    as_of_date: date
    created_at: datetime
