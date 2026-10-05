"""Tests for the get_db request-scoped session generator (signalscope.db.session)."""

from unittest.mock import MagicMock

import pytest

from signalscope.db import session as session_module
from signalscope.db.session import get_db


def test_get_db_yields_a_session_and_closes_it(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_session = MagicMock()
    fake_session_cls = MagicMock(return_value=fake_session)
    monkeypatch.setattr(session_module, "Session", fake_session_cls)
    monkeypatch.setattr(session_module, "get_engine", lambda: "fake-engine")

    gen = get_db()
    yielded = next(gen)

    assert yielded is fake_session
    fake_session_cls.assert_called_once_with(bind="fake-engine")
    fake_session.close.assert_not_called()

    # Exhausting the generator runs the `finally` block.
    with pytest.raises(StopIteration):
        next(gen)
    fake_session.close.assert_called_once()
