"""Request-scoped database session."""

from collections.abc import Generator

from sqlalchemy.orm import Session

from signalscope.db.engine import get_engine


def get_db() -> Generator[Session, None, None]:
    session = Session(bind=get_engine())
    try:
        yield session
    finally:
        session.close()
