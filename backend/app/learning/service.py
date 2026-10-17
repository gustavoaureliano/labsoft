from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.learning.models import Lesson
from app.learning.schemas import LessonCreate, LessonUpdate
from app.media import service as media_service


class LessonNotFound(LookupError):
    pass


class LessonPositionConflict(ValueError):
    pass


class MediaUnavailable(ValueError):
    pass


def lock_course(session: Session, course_id: str) -> None:
    if session.bind.dialect.name == "postgresql":
        session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:course, 0))"), {"course": course_id})


def get_lesson(session: Session, lesson_id: str) -> Lesson:
    lesson = session.get(Lesson, lesson_id)
    if lesson is None:
        raise LessonNotFound("Aula não encontrada")
    return lesson


def update_lesson(session: Session, lesson: Lesson, data: LessonUpdate) -> Lesson:
    lock_course(session, lesson.course_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        if value is None:
            raise ValueError("Campos da aula não podem ser nulos")
        setattr(lesson, key, value)
    session.commit()
    return lesson


def delete_lesson(session: Session, lesson: Lesson) -> None:
    lock_course(session, lesson.course_id)
    session.delete(lesson)
    session.commit()


def reorder_lessons(session: Session, course_id: str, lesson_ids: list[str]) -> list[Lesson]:
    lock_course(session, course_id)
    lessons = list_lessons(session, course_id)
    by_id = {lesson.id: lesson for lesson in lessons}
    if len(lesson_ids) != len(set(lesson_ids)) or set(lesson_ids) != set(by_id):
        raise ValueError("Envie todas as aulas do curso, uma vez cada")
    try:
        offset = max((lesson.position for lesson in lessons), default=0) + len(lessons) + 1
        for index, lesson in enumerate(lessons):
            lesson.position = offset + index
        session.flush()
        for index, lesson_id in enumerate(lesson_ids, 1):
            by_id[lesson_id].position = index
        session.commit()
    except Exception:
        session.rollback()
        raise
    return [by_id[lesson_id] for lesson_id in lesson_ids]


def create_lesson(session: Session, data: LessonCreate) -> Lesson:
    lock_course(session, data.course_id)
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


def associate_media(session: Session, lesson_id: str, media_id: UUID | None) -> Lesson:
    lesson = session.get(Lesson, lesson_id)
    if lesson is None:
        raise LessonNotFound("Aula não encontrada")
    lock_course(session, lesson.course_id)
    if media_id is not None:
        media = media_service.get_media(session, media_id)
        if media.status != "available":
            raise MediaUnavailable("A mídia precisa estar disponível para ser associada")
    lesson.media_id = media_id
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise
    return lesson
