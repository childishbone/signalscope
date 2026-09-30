"""Watchlist endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from signalscope.api.deps import require_admin
from signalscope.api.schemas import AddByProviderSymbolIn, QuoteOut, SecurityOut, WatchlistItemOut
from signalscope.db.models import Security, WatchlistItem
from signalscope.db.session import get_db
from signalscope.market_data.yahoo import YahooProvider
from signalscope.services.bars import compute_snapshot, refresh_bars
from signalscope.services.signal_history import record_signals
from signalscope.services.signals import compute_signals_for_security

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])

_provider = YahooProvider()


@router.get("", response_model=list[WatchlistItemOut])
def list_watchlist(db: Session = Depends(get_db)) -> list[WatchlistItemOut]:
    stmt = select(WatchlistItem).join(Security).order_by(Security.symbol)
    items = list(db.scalars(stmt))

    def to_out(item: WatchlistItem) -> WatchlistItemOut:
        snapshot = compute_snapshot(db, item.security_id)
        return WatchlistItemOut(
            id=item.id,
            added_at=item.added_at,
            security=SecurityOut.model_validate(item.security),
            quote=QuoteOut(**snapshot.__dict__) if snapshot else None,
        )

    return [to_out(item) for item in items]


@router.post(
    "",
    response_model=WatchlistItemOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def add_to_watchlist(
    payload: AddByProviderSymbolIn, db: Session = Depends(get_db)
) -> WatchlistItem:
    security = db.scalar(
        select(Security).where(Security.provider_symbol == payload.provider_symbol)
    )

    if security is None:
        matches = _provider.search_securities(payload.provider_symbol, limit=5)
        exact = next((m for m in matches if m.provider_symbol == payload.provider_symbol), None)
        if exact is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                f"'{payload.provider_symbol}' was not found in a supported market",
            )
        security = Security(
            symbol=exact.symbol,
            exchange_code=exact.exchange_code,
            exchange_name=exact.exchange_name,
            country=exact.country,
            currency=exact.currency,
            name=exact.name,
            asset_type=exact.asset_type,
            provider_symbol=exact.provider_symbol,
        )
        db.add(security)
        db.flush()  # assigns security.id without committing yet

    existing = db.scalar(select(WatchlistItem).where(WatchlistItem.security_id == security.id))
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Security is already on the watchlist")

    item = WatchlistItem(security_id=security.id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.post(
    "/{item_id}/refresh",
    dependencies=[Depends(require_admin)],
)
def refresh_watchlist_item(item_id: int, db: Session = Depends(get_db)) -> dict[str, int]:
    """Manual trigger for now; a later phase replaces this with a scheduled job.

    Refreshes stored price bars, then recomputes and persists this
    security's signals so signal history and change detection stay current.
    """
    item = db.get(WatchlistItem, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Watchlist item not found")

    bars_written = refresh_bars(db, item.security, _provider)

    signal_changes = 0
    signals = compute_signals_for_security(db, item.security_id)
    if signals is not None:
        signal_changes = len(record_signals(db, item.security_id, signals))

    return {"bars_written": bars_written, "signal_changes": signal_changes}


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def remove_from_watchlist(item_id: int, db: Session = Depends(get_db)) -> None:
    item = db.get(WatchlistItem, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Watchlist item not found")
    db.delete(item)
    db.commit()
