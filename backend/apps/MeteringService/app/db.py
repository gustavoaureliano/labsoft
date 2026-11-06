"""One shared Postgres instance, one schema per service (simulates a database per service).
Falls back to SQLite for local runs without Postgres."""
import os
import time
from datetime import datetime, timezone

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session

SCHEMA = "metering"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

engine = create_engine(DATABASE_URL)
IS_SQLITE = engine.dialect.name == "sqlite"
if IS_SQLITE:  # sqlite has no schemas
    engine = engine.execution_options(schema_translate_map={SCHEMA: None})


def utcnow() -> datetime:
    """Naive UTC, so timestamps behave the same on Postgres and SQLite."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    metadata = MetaData(schema=SCHEMA)


def init_db(retries: int = 30) -> None:
    for attempt in range(retries):
        try:
            if not IS_SQLITE:
                with engine.begin() as conn:
                    conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"))
            Base.metadata.create_all(engine)
            return
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(1)  # database may still be starting


def get_session():
    with Session(engine) as session:
        yield session
