from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.integrations import Course, Integrations, User
from app.learning.models import Lesson
from app.media.models import Media


def require_teacher(user: User) -> None:
    if user.role != "teacher":
        raise HTTPException(403, "Ação exclusiva do professor")


def require_course(user: User, integrations: Integrations, course_id: str, *, write: bool = False) -> Course:
    course = integrations.course(course_id)
    if course is None:
        raise HTTPException(404, "Curso não encontrado")
    if course.moderation_status != "visible":
        raise HTTPException(403, "Curso indisponível por decisão de moderação")
    if user.role == "teacher" and course.owner_id == user.id:
        return course
    if not write and user.role == "student" and course.published and integrations.has_access(user.id, course_id):
        return course
    raise HTTPException(403, "Sem acesso ao curso")


def require_media(user: User, integrations: Integrations, session: Session, media: Media) -> None:
    lessons = session.scalars(select(Lesson).where(
        or_(Lesson.media_id == media.id, Lesson.thumbnail_id == media.id)
    )).all()
    if not lessons and user.role == "teacher" and media.owner_id == user.id:
        return
    # A direct media URL must not bypass moderation, including an owner's preview.
    allowed = False
    for lesson in lessons:
        course = integrations.course(lesson.course_id)
        if lesson.moderation_status != "visible" or course and course.moderation_status != "visible":
            raise HTTPException(403, "Mídia indisponível por decisão de moderação")
        if course is None:
            continue
        if (
            (user.role == "teacher" and course.owner_id == user.id)
            or (user.role == "student" and course.published and integrations.has_access(user.id, lesson.course_id))
        ):
            allowed = True
    if not allowed:
        raise HTTPException(403, "Sem acesso à mídia")
