"""Shared pytest fixtures."""

import pytest

from signalscope.config import get_settings
from signalscope.db.engine import get_engine


@pytest.fixture()
def db_session():
    settings = get_settings()
    if not settings.database_url:
        pytest.skip("DATABASE_URL not set; skipping tests that need a real database")

    connection = get_engine().connect()
    transaction = connection.begin()
    from sqlalchemy.orm import Session

    session = Session(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
