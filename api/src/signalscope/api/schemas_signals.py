"""Response schemas for the technical-analysis signals endpoint."""

from pydantic import BaseModel

from signalscope.api.schemas import SecurityOut
from signalscope.signals.types import SignalState


class IndicatorResultOut(BaseModel):
    state: SignalState
    score: float
    reasons: list[str]
    values: dict[str, float]


class SecuritySignalsOut(BaseModel):
    security: SecurityOut
    bars_used: int
    dma: IndicatorResultOut
    rsi: IndicatorResultOut
    ichimoku: IndicatorResultOut
    elliott: IndicatorResultOut
    overall: IndicatorResultOut
