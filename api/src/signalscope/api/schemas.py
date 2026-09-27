"""Pydantic request/response models for the API."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SecurityIn(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    exchange_code: str = Field(min_length=1, max_length=10)
    exchange_name: str = Field(min_length=1)
    country: str = Field(min_length=2, max_length=2)
    currency: str = Field(min_length=3, max_length=3)
    name: str = Field(min_length=1)
    asset_type: Literal["equity", "etf"] = "equity"
    provider_symbol: str = Field(min_length=1)


class SecurityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    exchange_code: str
    exchange_name: str
    country: str
    currency: str
    name: str
    asset_type: str
    provider_symbol: str


class QuoteOut(BaseModel):
    latest_price: Decimal
    latest_date: date
    change: Decimal
    change_pct: Decimal
    volume: int
    high_52w: Decimal
    low_52w: Decimal


class WatchlistItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    added_at: datetime
    security: SecurityOut
    quote: QuoteOut | None = None


class SecurityMatchOut(BaseModel):
    """One search result. Field names match market_data.types.SecurityMatch."""

    symbol: str
    provider_symbol: str
    name: str
    exchange_code: str
    exchange_name: str
    country: str
    currency: str
    asset_type: str


class AddByProviderSymbolIn(BaseModel):
    """What the Watchlist page actually sends: just the ticker the user picked."""

    provider_symbol: str = Field(min_length=1, max_length=20)
