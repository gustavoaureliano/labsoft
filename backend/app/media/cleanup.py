"""Explicit unassociated-media cleanup. Defaults to dry-run."""

import argparse
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.integrations import get_integrations
from app.learning.models import Lesson, LessonProgress
from app.media.models import Media
from app.media.storage import get_video_path


def cleanup(session: Session, owner_id: str, minimum_age_hours: int, *, apply: bool = False) -> list[str]:
    if minimum_age_hours < 1:
        raise ValueError("Idade mínima deve ser pelo menos uma hora")
    cutoff = datetime.now(timezone.utc) - timedelta(hours=minimum_age_hours)
    candidates = list(session.scalars(select(Media).where(
        Media.owner_id == owner_id, Media.created_at < cutoff
    ).with_for_update(skip_locked=True)))
    removed = []
    for media in candidates:
        reference = session.scalar(select(Lesson.id).where(or_(
            Lesson.media_id == media.id, Lesson.thumbnail_id == media.id
        )).limit(1))
        if reference is not None:
            continue
        if session.scalar(select(LessonProgress.lesson_id).where(LessonProgress.media_id == media.id).limit(1)) is not None:
            continue
        removed.append(str(media.id))
        if apply:
            try:
                path = get_video_path(media.storage_key)
            except FileNotFoundError:
                # Missing files can be cleaned; invalid paths must never be unlinked.
                path = None
            if path is not None:
                path.unlink()
            session.delete(media)
    if apply:
        session.commit()
    else:
        session.rollback()
    return removed


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("owner_id")
    parser.add_argument("--minimum-age-hours", type=int, default=24)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    owner = get_integrations().user(args.owner_id)
    if owner is None or owner.role != "teacher":
        parser.error("Professor inválido")
    with SessionLocal() as session:
        print({"apply": args.apply, "media_ids": cleanup(session, owner.id, args.minimum_age_hours, apply=args.apply)})
