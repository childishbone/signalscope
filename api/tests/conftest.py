"""Shared pytest fixtures."""

import pytest
from sqlalchemy.orm import Session

from signalscope.config import get_settings
from signalscope.db.engine import get_engine


@pytest.fixture()
def db_session():
    """A database session whose changes are always rolled back, even if the
    code under test calls session.commit() (join_transaction_mode="create_savepoint"
    makes commit() release a savepoint instead of the real outer transaction).
    """
    settings = get_settings()
    if not settings.database_url:
        pytest.skip("DATABASE_URL not set; skipping tests that need a real database")

    connection = get_engine().connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()