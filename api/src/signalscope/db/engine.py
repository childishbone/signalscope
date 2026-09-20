"""Shared SQLAlchemy engine."""

from functools import lru_cache

from sqlalchemy import Engine, create_engine

from signalscope.config import get_database_url


@lru_cache
def get_engine() -> Engine:
    """One engine per process.

    Neon suspends idle compute after 5 minutes, so we recycle connections
    and ping before use to avoid handing out a dead one.
    """
    return create_engine(get_database_url(), pool_pre_ping=True, pool_recycle=300)
