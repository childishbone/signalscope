"""Technical-analysis signals endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from signalscope.api.schemas import SecurityOut
from signalscope.api.schemas_signals import IndicatorResultOut, SecuritySignalsOut
from signalscope.db.models import Security
from signalscope.db.session import get_db
from signalscope.services.signals import MINIMUM_BARS_REQUIRED, compute_signals_for_security
from signalscope.signals.types import IndicatorResult

router = APIRouter(prefix="/api/securities", tags=["signals"])


def _to_indicator_out(result: IndicatorResult) -> IndicatorResultOut:
    return IndicatorResultOut(
        state=result.state,
        score=result.score,
        reasons=result.reasons,
        values=result.values,
    )


@router.get("/{security_id}/signals", response_model=SecuritySignalsOut)
def get_security_signals(security_id: int, db: Session = Depends(get_db)) -> SecuritySignalsOut:
    security = db.get(Security, security_id)
    if security is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Security not found")

    signals = compute_signals_for_security(db, security_id)
    if signals is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Not enough historical price data yet to compute signals; need "
            f"at least {MINIMUM_BARS_REQUIRED} daily bars.",
        )

    return SecuritySignalsOut(
        security=SecurityOut.model_validate(security),
        bars_used=signals.bars_used,
        dma=_to_indicator_out(signals.dma),
        rsi=_to_indicator_out(signals.rsi),
        ichimoku=_to_indicator_out(signals.ichimoku),
        elliott=_to_indicator_out(signals.elliott),
        overall=_to_indicator_out(signals.overall),
    )
