"""Role and ownership permission checks for Daniel's modules."""

from fastapi import HTTPException

from app.integrations import Course, Integrations, LessonRef, User


def require_student(user: User) -> None:
    if user.role != "student":
        raise HTTPException(403, "Ação exclusiva do aluno")


def require_teacher(user: User) -> None:
    if user.role != "teacher":
        raise HTTPException(403, "Ação exclusiva do professor")


def require_admin(user: User) -> None:
    if user.role != "admin":
        raise HTTPException(403, "Ação exclusiva do administrador")


def require_course_access(
    user: User, integrations: Integrations, course_id: str, *, write: bool = False
) -> Course:
    course = integrations.course(course_id)
    if course is None:
        raise HTTPException(404, "Curso não encontrado")
    if user.role == "teacher" and course.owner_id == user.id:
        return course
    if (
        not write
        and user.role == "student"
        and course.published
        and integrations.has_access(user.id, course_id)
    ):
        return course
    raise HTTPException(403, "Sem acesso ao curso")


def require_lesson_access(
    user: User, integrations: Integrations, lesson_id: str
) -> LessonRef:
    lesson = integrations.lesson(lesson_id)
    if lesson is None:
        raise HTTPException(404, "Aula não encontrada")
    require_course_access(user, integrations, lesson.course_id)
    return lesson
