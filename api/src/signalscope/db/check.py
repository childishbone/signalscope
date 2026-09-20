"""Connectivity check. Run with: python -m signalscope.db.check"""

from sqlalchemy import text

from signalscope.db.engine import get_engine


def main() -> None:
    with get_engine().connect() as conn:
        version = conn.execute(text("select version()")).scalar_one()
        database = conn.execute(text("select current_database()")).scalar_one()
        now = conn.execute(text("select now()")).scalar_one()
    print(f"Connected to database '{database}' at {now}")
    print(version)


if __name__ == "__main__":
    main()
