from __future__ import annotations

import hashlib
from datetime import timedelta

from sqlalchemy import case
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from ..models import RateLimitBucket, utcnow


class RateLimitService:

    def consume(
        self,
        db: Session,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> bool:
        now = utcnow()
        reset_before = now - timedelta(seconds=window_seconds)
        key_hash = hashlib.sha256(
            key.encode("utf-8")
        ).hexdigest()
        values = {
            "key_hash": key_hash,
            "window_started_at": now,
            "attempts": 1,
        }
        dialect = db.get_bind().dialect.name
        if dialect == "postgresql":
            insert = pg_insert(RateLimitBucket)
        elif dialect == "sqlite":
            insert = sqlite_insert(RateLimitBucket)
        else:
            raise RuntimeError(
                f"Rate limiting is unsupported for {dialect}."
            )

        statement = insert.values(**values).on_conflict_do_update(
            index_elements=[RateLimitBucket.key_hash],
            set_={
                "window_started_at": case(
                    (
                        RateLimitBucket.window_started_at <= reset_before,
                        now,
                    ),
                    else_=RateLimitBucket.window_started_at,
                ),
                "attempts": case(
                    (
                        RateLimitBucket.window_started_at <= reset_before,
                        1,
                    ),
                    else_=RateLimitBucket.attempts + 1,
                ),
            },
        ).returning(RateLimitBucket.attempts)
        attempts = db.scalar(statement)
        return attempts is not None and attempts <= limit
