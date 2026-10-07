"""Response schemas for the CANSLIM checklist endpoint."""

from pydantic import BaseModel

from signalscope.api.schemas import SecurityOut
from signalscope.signals.canslim_types import CanslimVerdict


class CanslimConstituentOut(BaseModel):
    symbol: str
    name: str
    weight_pct: float
    verdict: CanslimVerdict


class CanslimLetterOut(BaseModel):
    letter: str
    verdict: CanslimVerdict
    reasons: list[str]
    values: dict[str, float]
    constituents: list[CanslimConstituentOut] | None = None


class SecurityCanslimOut(BaseModel):
    security: SecurityOut
    letters: dict[str, CanslimLetterOut]
    score_pct: float | None
    criteria_evaluated: int
    criteria_total: int
