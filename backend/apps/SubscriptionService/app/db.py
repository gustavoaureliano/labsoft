"""Subscription persistence; Alembic owns schema changes, runtime only checks tables."""
import os
from datetime import datetime, timezone

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session

SCHEMA = "subscription"
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
    # Provisioning and schema changes are explicit Alembic commands, not runtime DDL.
    prefix = "" if IS_SQLITE else f"{SCHEMA}."
    with engine.connect() as conn:
        conn.execute(text(f"SELECT user_id, item_id FROM {prefix}subscription LIMIT 0"))


def get_session():
    with Session(engine) as session:
        yield session
