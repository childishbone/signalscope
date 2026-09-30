"""Batch-refresh every watchlist security: pull fresh price bars,
recompute signals, and persist any state changes.

Runs on a schedule (see .github/workflows/scheduled-refresh.yml) so
signal history builds up automatically; the Watchlist page's "Refresh
data" button remains for refreshing a single security on demand.
"""

from __future__ import annotations

import sys
import traceback
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from signalscope.db.engine import get_engine
from signalscope.db.models import IngestionRun, WatchlistItem
from signalscope.market_data.yahoo import YahooProvider
from signalscope.services.bars import refresh_bars
from signalscope.services.signal_history import record_signals
from signalscope.services.signals import compute_signals_for_security


@dataclass(frozen=True)
class RunSummary:
    """A plain snapshot of the run's outcome, safe to read after the
    database session that produced it has closed."""

    status: str
    securities_total: int
    securities_failed: int
    bars_upserted: int


def run(db: Session) -> RunSummary:
    run_row = IngestionRun(triggered_by="schedule")
    db.add(run_row)
    db.commit()
    db.refresh(run_row)

    provider = YahooProvider()
    items = list(db.scalars(select(WatchlistItem)))
    run_row.securities_total = len(items)

    failures = 0
    bars_upserted = 0
    error_lines: list[str] = []

    for item in items:
        try:
            bars_upserted += refresh_bars(db, item.security, provider)
            signals = compute_signals_for_security(db, item.security_id)
            if signals is not None:
                record_signals(db, item.security_id, signals)
        except Exception as exc:
            # One bad security (e.g. a temporary Yahoo hiccup) must not
            # abort the whole batch, and the failed transaction must be
            # rolled back before the next security's queries can run.
            db.rollback()
            failures += 1
            error_lines.append(f"{item.security.symbol}: {exc}")
            print(f"[refresh_watchlist] {item.security.symbol} failed: {exc}", file=sys.stderr)
            traceback.print_exc()

    run_row.securities_failed = failures
    run_row.bars_upserted = bars_upserted
    run_row.error_summary = "\n".join(error_lines) or None
    if failures == 0:
        status = "succeeded"
    elif failures < len(items):
        status = "partial"
    else:
        status = "failed"
    run_row.status = status
    run_row.finished_at = datetime.now(UTC)

    db.commit()
    return RunSummary(
        status=status,
        securities_total=len(items),
        securities_failed=failures,
        bars_upserted=bars_upserted,
    )


def main() -> None:
    with Session(bind=get_engine()) as db:
        summary = run(db)

    print(
        f"[refresh_watchlist] status={summary.status} "
        f"securities_total={summary.securities_total} "
        f"securities_failed={summary.securities_failed} "
        f"bars_upserted={summary.bars_upserted}"
    )
    if summary.status == "failed":
        sys.exit(1)


if __name__ == "__main__":
    main()
