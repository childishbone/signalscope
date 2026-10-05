"""Tests for the require_admin dependency (signalscope.api.deps)."""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from signalscope.api import deps as deps_module
from signalscope.api.deps import require_admin


def test_require_admin_raises_503_when_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(deps_module, "get_settings", lambda: SimpleNamespace(admin_api_key=""))
    with pytest.raises(HTTPException) as exc_info:
        require_admin(x_admin_key="anything")
    assert exc_info.value.status_code == 503


def test_require_admin_raises_401_when_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        deps_module, "get_settings", lambda: SimpleNamespace(admin_api_key="secret")
    )
    with pytest.raises(HTTPException) as exc_info:
        require_admin(x_admin_key=None)
    assert exc_info.value.status_code == 401


def test_require_admin_raises_401_when_key_wrong(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        deps_module, "get_settings", lambda: SimpleNamespace(admin_api_key="secret")
    )
    with pytest.raises(HTTPException) as exc_info:
        require_admin(x_admin_key="wrong-key")
    assert exc_info.value.status_code == 401


def test_require_admin_passes_when_key_correct(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        deps_module, "get_settings", lambda: SimpleNamespace(admin_api_key="secret")
    )
    # Should not raise.
    require_admin(x_admin_key="secret")
