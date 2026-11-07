"""QuestionService implementation (F29, F30, F31)."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.communication import notifications as notification_service
from app.communication.models import Question
from app.communication.schemas import QuestionResponse
from app.integrations import Integrations, User
from app.permissions import require_course_access, require_student, require_teacher


class QuestionNotFound(Exception):
    pass


class QuestionAccessDenied(Exception):
    pass


def _serialize_question(question: Question, integrations: Integrations) -> QuestionResponse:
    course = integrations.course(question.course_id)
    lesson = integrations.lesson(question.lesson_id) if question.lesson_id else None
    if lesson is not None:
        prefix = f"Aula {lesson.position:02d} — "
        lesson_title = (
            lesson.title
            if lesson.title.startswith("Aula")
            else f"{prefix}{lesson.title}"
        )
    else:
        lesson_title = "Dúvida geral sobre o curso"
    return QuestionResponse(
        id=question.id,
        student_id=question.student_id,
        student_name=question.student_name,
        course_id=question.course_id,
        course_title=course.title if course else question.course_id,
        lesson_id=question.lesson_id,
        lesson_title=lesson_title,
        teacher_id=question.teacher_id,
        teacher_name=course.teacher if course else question.teacher_id,
        prompt=question.prompt,
        status=question.status,  # type: ignore[arg-type]
        answer=question.answer,
        created_at=question.created_at,
        answered_at=question.answered_at,
    )


def criar_duvida_privada(
    session: Session,
    integrations: Integrations,
    user: User,
    course_id: str,
    lesson_id: str | None,
    prompt: str,
) -> QuestionResponse:
    """F29 — Enviar dúvida privada sobre curso ou aula e notificar o professor responsável."""
    require_student(user)
    course = require_course_access(user, integrations, course_id)
    if lesson_id is not None:
        lesson = integrations.lesson(lesson_id)
        if lesson is None or lesson.course_id != course_id:
            raise QuestionNotFound("Aula não encontrada neste curso")

    question = Question(
        student_id=user.id,
        student_name=user.name,
        course_id=course.id,
        lesson_id=lesson_id,
        teacher_id=course.owner_id,
        prompt=prompt,
        status="pending",
    )
    session.add(question)
    session.flush()
    notification_service.notificar_professor(
        session, course.owner_id, question.id, course.title
    )
    session.commit()
    session.refresh(question)
    return _serialize_question(question, integrations)


def consultar_duvidas_do_aluno(
    session: Session, integrations: Integrations, user: User
) -> list[QuestionResponse]:
    """F30 — Acompanhar dúvidas privadas do aluno autenticado."""
    require_student(user)
    rows = session.scalars(
        select(Question)
        .where(Question.student_id == user.id)
        .order_by(Question.created_at.desc(), Question.id.desc())
    )
    return [_serialize_question(row, integrations) for row in rows]


def buscar_duvidas_destinadas(
    session: Session,
    integrations: Integrations,
    user: User,
    status_filter: str = "all",
) -> list[QuestionResponse]:
    """F31 — Listar dúvidas vinculadas aos cursos do professor (filtrando pendentes/respondidas)."""
    require_teacher(user)
    stmt = select(Question).where(Question.teacher_id == user.id)
    if status_filter in {"pending", "answered"}:
        stmt = stmt.where(Question.status == status_filter)
    stmt = stmt.order_by(Question.created_at.desc(), Question.id.desc())
    rows = session.scalars(stmt)
    return [_serialize_question(row, integrations) for row in rows]


def registrar_resposta(
    session: Session,
    integrations: Integrations,
    user: User,
    question_id: str,
    answer: str,
) -> QuestionResponse:
    """F31 — Responder dúvida, atualizar estado para respondida e notificar o aluno."""
    require_teacher(user)
    question = session.get(Question, question_id)
    if question is None:
        raise QuestionNotFound("Dúvida não encontrada")
    if question.teacher_id != user.id:
        raise QuestionAccessDenied("Esta dúvida não pertence aos cursos deste professor")

    question.answer = answer
    question.status = "answered"
    question.answered_at = datetime.now(timezone.utc)
    course = integrations.course(question.course_id)
    notification_service.notificar_aluno(
        session,
        question.student_id,
        question.id,
        course.title if course else question.course_id,
    )
    session.commit()
    session.refresh(question)
    return _serialize_question(question, integrations)
