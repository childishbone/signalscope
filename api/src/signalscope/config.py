"""Application settings, read from environment variables (and api/.env locally)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


def to_sqlalchemy_url(url: str) -> str:
    """Neon gives postgresql://; SQLAlchemy must be told to use the psycopg 3 driver."""
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix) :]
    return url


def get_database_url() -> str:
    url = get_settings().database_url
    if not url:
        raise RuntimeError("DATABASE_URL is not set. Add it to api/.env (see .env.example).")
    return to_sqlalchemy_url(url)
