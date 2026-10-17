from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.learning.models import Lesson
from app.learning.schemas import LessonCreate
from app.media import service as media_service


class LessonNotFound(LookupError):
    pass


class LessonPositionConflict(ValueError):
    pass


class MediaUnavailable(ValueError):
    pass


def create_lesson(session: Session, data: LessonCreate) -> Lesson:
    lesson = Lesson(**data.model_dump())
    session.add(lesson)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        # Only a position conflict should become a client-facing conflict.
        existing = session.scalar(select(Lesson).where(
            Lesson.course_id == data.course_id, Lesson.position == data.position
        ))
        if existing is not None:
            raise LessonPositionConflict("Já existe uma aula nessa posição do curso") from exc
        raise
    return lesson


def list_lessons(session: Session, course_id: str) -> list[Lesson]:
    return list(session.scalars(
        select(Lesson).where(Lesson.course_id == course_id).order_by(Lesson.position)
    ))


def get_playback(session: Session, lesson_id: str) -> Lesson:
    lesson = session.get(Lesson, lesson_id)
    if lesson is None:
        raise LessonNotFound("Aula não encontrada")
    if lesson.media_id is None:
        raise MediaUnavailable("A aula ainda não possui vídeo")
    # Reuse media availability and storage checks rather than duplicating them.
    media_service.get_video_content(session, lesson.media_id)
    return lesson


def associate_media(session: Session, lesson_id: str, media_id: UUID) -> Lesson:
    lesson = session.get(Lesson, lesson_id)
    if lesson is None:
        raise LessonNotFound("Aula não encontrada")
    media = media_service.get_media(session, media_id)
    if media.status != "available":
        raise MediaUnavailable("A mídia precisa estar disponível para ser associada")
    lesson.media_id = media.id
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise
    return lesson
