import os
from collections.abc import Callable, Iterator
from typing import TypeVar

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

T = TypeVar("T")


class Base(DeclarativeBase):
    pass

engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def get_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


def commit_with_retry(session: Session, stage: Callable[[], T]) -> T:
    """Stage a get-or-create write and commit it, retrying once on a unique-key race.

    ``stage`` must look the row up again before inserting, so that the retry
    after a concurrent insert takes the update path instead of failing with 500.
    """
    try:
        # Autoflush may raise the conflict inside stage() as well as on commit.
        result = stage()
        session.commit()
    except IntegrityError:
        session.rollback()
        result = stage()
        session.commit()
    return result
