"""Watchlist endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from signalscope.api.deps import require_admin
from signalscope.api.schemas import SecurityIn, WatchlistItemOut
from signalscope.db.models import Security, WatchlistItem
from signalscope.db.session import get_db

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


@router.get("", response_model=list[WatchlistItemOut])
def list_watchlist(db: Session = Depends(get_db)) -> list[WatchlistItem]:
    stmt = select(WatchlistItem).join(Security).order_by(Security.symbol)
    return list(db.scalars(stmt))


@router.post(
    "",
    response_model=WatchlistItemOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def add_to_watchlist(payload: SecurityIn, db: Session = Depends(get_db)) -> WatchlistItem:
    security = db.scalar(
        select(Security).where(
            Security.exchange_code == payload.exchange_code,
            Security.symbol == payload.symbol,
        )
    )
    if security is None:
        security = Security(**payload.model_dump())
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
