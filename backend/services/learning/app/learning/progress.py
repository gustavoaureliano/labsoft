from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.learning.models import Lesson, LessonProgress
from app.learning.schemas import ProgressResponse
from app.learning.service import MediaUnavailable, get_lesson, lock_course
from app.media import service as media_service


def get_progress(session: Session, student_id: str, lesson: Lesson) -> ProgressResponse:
    row = session.get(LessonProgress, (student_id, lesson.id))
    if row is None or row.media_id != lesson.media_id:
        return ProgressResponse(position_seconds=0, completed=False)
    return ProgressResponse(position_seconds=row.position_seconds, completed=row.completed_at is not None, updated_at=row.updated_at)


def save_progress(session: Session, student_id: str, lesson_id: str, media_id: UUID, position: float) -> ProgressResponse:
    lesson = get_lesson(session, lesson_id)
    lock_course(session, lesson.course_id)
    session.refresh(lesson)
    if lesson.media_id != media_id:
        raise MediaUnavailable("O vídeo da aula mudou; recarregue a aula")
    media = media_service.get_media(session, media_id)
    if media.status != "available" or media.duration_seconds is None:
        raise MediaUnavailable("Vídeo ainda sem duração verificada")
    if position > media.duration_seconds:
        raise ValueError("Posição excede a duração do vídeo")
    row = session.get(LessonProgress, (student_id, lesson_id))
    if row is None:
        row = LessonProgress(student_id=student_id, lesson_id=lesson_id, media_id=media_id, position_seconds=0)
        session.add(row)
    if row.media_id != media_id:
        row.completed_at = None
        row.media_id = media_id
    now = datetime.now(timezone.utc)
    row.position_seconds = position
    row.updated_at = now
    if row.completed_at is None and position >= media.duration_seconds * 0.9:
        row.completed_at = now
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise
    return get_progress(session, student_id, lesson)
