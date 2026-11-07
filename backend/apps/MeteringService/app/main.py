from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from .db import Base, get_session, init_db, utcnow

HEARTBEAT_INTERVAL_S = 10  # each beat counts as this many seconds watched


class Beat(Base):
    __tablename__ = "beat"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(index=True)
    item_id: Mapped[int] = mapped_column(index=True)
    stamp: Mapped[int]  # playback position in seconds
    created_at: Mapped[datetime] = mapped_column(default=utcnow, index=True)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Metering", lifespan=lifespan)


class BeatIn(BaseModel):
    user_id: int
    item_id: int
    stamp: int


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/heartbeat", status_code=202)
def heartbeat(beat: BeatIn, db: Session = Depends(get_session)) -> dict[str, str]:
    db.add(Beat(**beat.model_dump()))
    db.commit()
    return {"status": "accepted"}


@app.get("/api/usage/summary")
def summary(from_: datetime = Query(alias="from"), to: datetime = Query(), db: Session = Depends(get_session)) -> dict:
    """Watch time per item in [from, to). Input for teacher payouts."""
    rows = db.execute(
        select(Beat.item_id, func.count()).where(Beat.created_at >= from_, Beat.created_at < to).group_by(Beat.item_id)
    ).all()
    return {"items": [{"item_id": i, "beats": n, "seconds": n * HEARTBEAT_INTERVAL_S} for i, n in rows]}


@app.get("/api/usage/{user_id}/{item_id}")
def usage(user_id: int, item_id: int, db: Session = Depends(get_session)) -> dict:
    where = (Beat.user_id == user_id, Beat.item_id == item_id)
    beats = db.scalar(select(func.count()).select_from(Beat).where(*where))
    last = db.scalar(select(Beat.stamp).where(*where).order_by(Beat.id.desc()).limit(1))
    return {
        "user_id": user_id,
        "item_id": item_id,
        "beats": beats,
        "seconds_watched": beats * HEARTBEAT_INTERVAL_S,
        "last_position": last,
    }
