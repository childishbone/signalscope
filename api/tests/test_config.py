from signalscope.config import to_sqlalchemy_url


def test_postgresql_scheme_gets_psycopg_driver() -> None:
    url = "postgresql://u:p@host/db?sslmode=require"
    assert to_sqlalchemy_url(url) == "postgresql+psycopg://u:p@host/db?sslmode=require"


def test_short_postgres_scheme_is_normalised() -> None:
    assert to_sqlalchemy_url("postgres://u:p@host/db").startswith("postgresql+psycopg://")


def test_already_qualified_url_is_unchanged() -> None:
    url = "postgresql+psycopg://u:p@host/db"
    assert to_sqlalchemy_url(url) == url
