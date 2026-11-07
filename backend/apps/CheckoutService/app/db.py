"""One shared Postgres instance, one schema per service (simulates a database per service).
Falls back to SQLite for local runs without Postgres."""
import os
from datetime import datetime, timezone

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session

SCHEMA = "checkout"
DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(DATABASE_URL)
IS_SQLITE = engine.dialect.name == "sqlite"
if IS_SQLITE:  # sqlite has no schemas
    engine = engine.execution_options(schema_translate_map={SCHEMA: None})


def utcnow() -> datetime:
    """Naive UTC, so timestamps behave the same on Postgres and SQLite."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    metadata = MetaData(schema=SCHEMA)


def init_db() -> None:
    prefix = "" if IS_SQLITE else f"{SCHEMA}."
    with engine.connect() as conn:
        conn.execute(text(f"SELECT id FROM {prefix}checkout LIMIT 0"))


def get_session():
    with Session(engine) as session:
        yield session
