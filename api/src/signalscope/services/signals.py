"""Computing technical-analysis signals for a security from its stored bars."""

from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from signalscope.db.models import DailyBar
from signalscope.signals.bollinger import MINIMUM_CLOSES_REQUIRED as BOLLINGER_MINIMUM_REQUIRED
from signalscope.signals.bollinger import score_bollinger
from signalscope.signals.dma import MINIMUM_CLOSES_REQUIRED as DMA_MINIMUM_REQUIRED
from signalscope.signals.dma import score_dma
from signalscope.signals.ichimoku import MINIMUM_BARS_REQUIRED as ICHIMOKU_MINIMUM_REQUIRED
from signalscope.signals.ichimoku import score_ichimoku
from signalscope.signals.overall import compute_overall
from signalscope.signals.rsi import MINIMUM_CLOSES_REQUIRED as RSI_MINIMUM_REQUIRED
from signalscope.signals.rsi import score_rsi
from signalscope.signals.types import IndicatorResult

# The largest of the four indicators' own minimums -- Overall needs all
# four computed, so this is the floor for the whole endpoint.
MINIMUM_BARS_REQUIRED = max(
    DMA_MINIMUM_REQUIRED,
    RSI_MINIMUM_REQUIRED,
    ICHIMOKU_MINIMUM_REQUIRED,
    BOLLINGER_MINIMUM_REQUIRED,
)


@dataclass(frozen=True)
class SecuritySignals:
    """All five computed signals for one security, plus how many stored
    bars were used to compute them and the trading day they're as of."""

    dma: IndicatorResult
    rsi: IndicatorResult
    ichimoku: IndicatorResult
    bollinger: IndicatorResult
    overall: IndicatorResult
    bars_used: int
    as_of_date: date


def compute_signals_for_security(db: Session, security_id: int) -> SecuritySignals | None:
    """Compute all five signals for a security from its stored daily bars.

    Returns None if there isn't yet enough price history stored to compute
    every indicator; the caller is expected to turn that into a 422.
    """
    stmt = (
        select(DailyBar)
        .where(DailyBar.security_id == security_id)
        .order_by(DailyBar.trade_date.asc())
    )
    bars = list(db.scalars(stmt))

    if len(bars) < MINIMUM_BARS_REQUIRED:
        return None

    closes = [float(bar.close) for bar in bars]
    highs = [float(bar.high) for bar in bars]
    lows = [float(bar.low) for bar in bars]

    dma = score_dma(closes)
    rsi = score_rsi(closes)
    ichimoku = score_ichimoku(highs, lows, closes)
    bollinger = score_bollinger(closes)
    overall = compute_overall(dma=dma, rsi=rsi, ichimoku=ichimoku, bollinger=bollinger)

    return SecuritySignals(
        dma=dma,
        rsi=rsi,
        ichimoku=ichimoku,
        bollinger=bollinger,
        overall=overall,
        bars_used=len(bars),
        as_of_date=bars[-1].trade_date,
    )
