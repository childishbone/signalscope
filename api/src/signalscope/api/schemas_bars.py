"""Response schema for the price-history (bars) endpoint."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class DailyBarOut(BaseModel):
    trade_date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
