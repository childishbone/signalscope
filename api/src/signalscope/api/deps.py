"""Shared FastAPI dependencies."""

import hmac

from fastapi import Header, HTTPException, status

from signalscope.config import get_settings


def require_admin(x_admin_key: str | None = Header(default=None)) -> None:
    """FastAPI turns the parameter name x_admin_key into the header X-Admin-Key."""
    settings = get_settings()
    if not settings.admin_api_key:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Admin key not configured on the server"
        )
    if not x_admin_key or not hmac.compare_digest(x_admin_key, settings.admin_api_key):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or missing admin key")
