"""TeacherAnalyticsService implementation (F26, F41)."""

from typing import Literal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.analytics.schemas import (
    CourseAnalyticsItem,
    MetricIndicator,
    TeacherAnalyticsResponse,
)
from app.communication.models import Question
from app.integrations import Course, Integrations, User
from app.library_interaction.models import ContentRating
from app.permissions import require_course_access, require_teacher


def recalcular_media_avaliacoes(
    session: Session,
    target_type: Literal["lesson", "course"],
    target_id: str,
) -> tuple[float, int]:
    """F26 — Calcular nova média e quantidade total de avaliações do conteúdo."""
    row = session.execute(
        select(
            func.avg(ContentRating.stars),
            func.count(ContentRating.id),
        ).where(
            ContentRating.target_type == target_type,
            ContentRating.target_id == target_id,
        )
    ).one()
    avg_stars = round(float(row[0]), 2) if row[0] is not None else 0.0
    total = int(row[1] or 0)
    return avg_stars, total


def _course_ratings_summary(
    session: Session, integrations: Integrations, course_id: str
) -> tuple[float, int]:
    lesson_ids = [lesson.id for lesson in integrations.course_lessons(course_id)]
    conditions = [
        (ContentRating.target_type == "course") & (ContentRating.target_id == course_id)
    ]
    if lesson_ids:
        conditions.append(
            (ContentRating.target_type == "lesson")
            & (ContentRating.target_id.in_(lesson_ids))
        )
    row = session.execute(
        select(
            func.avg(ContentRating.stars),
            func.count(ContentRating.id),
        ).where(or_(*conditions))
    ).one()
    avg_stars = round(float(row[0]), 2) if row[0] is not None else 0.0
    total = int(row[1] or 0)
    return avg_stars, total


def obter_indicadores_professor(
    session: Session,
    integrations: Integrations,
    user: User,
    period: Literal["30d", "90d", "365d"] = "30d",
    course_id: str | None = None,
) -> TeacherAnalyticsResponse:
    """F41 — Validar propriedade dos cursos do professor e consolidar métricas com origem dos indicadores."""
    require_teacher(user)

    if course_id is not None:
        course = require_course_access(user, integrations, course_id, write=True)
        teacher_courses: list[Course] = [course]
    else:
        teacher_courses = [
            c for c in integrations.courses() if c.owner_id == user.id
        ]

    course_items: list[CourseAnalyticsItem] = []
    total_enrollments = 0
    total_active = 0
    completion_rates: list[float] = []
    weighted_rating_sum = 0.0
    total_ratings_count = 0
    total_pending_q = 0
    total_answered_q = 0

    for course in teacher_courses:
        snapshot = integrations.course_engagement_snapshot(course.id, period)
        avg_rating, rating_count = _course_ratings_summary(
            session, integrations, course.id
        )
        pending_q = int(
            session.scalar(
                select(func.count(Question.id)).where(
                    Question.course_id == course.id,
                    Question.status == "pending",
                )
            )
            or 0
        )
        answered_q = int(
            session.scalar(
                select(func.count(Question.id)).where(
                    Question.course_id == course.id,
                    Question.status == "answered",
                )
            )
            or 0
        )

        enrollments = int(snapshot["enrollments"])
        active_students = int(snapshot["active_students"])
        completion_rate = float(snapshot["completion_rate"])

        total_enrollments += enrollments
        total_active += active_students
        completion_rates.append(completion_rate)
        weighted_rating_sum += avg_rating * rating_count
        total_ratings_count += rating_count
        total_pending_q += pending_q
        total_answered_q += answered_q

        course_items.append(
            CourseAnalyticsItem(
                course_id=course.id,
                course_title=course.title,
                enrollments=enrollments,
                active_students=active_students,
                completion_rate=completion_rate,
                avg_watch_minutes=int(snapshot["avg_watch_minutes"]),
                average_rating=avg_rating,
                total_ratings=rating_count,
                pending_questions=pending_q,
                answered_questions=answered_q,
            )
        )

    overall_completion = (
        round(sum(completion_rates) / len(completion_rates), 2)
        if completion_rates
        else 0.0
    )
    overall_rating = (
        round(weighted_rating_sum / total_ratings_count, 2)
        if total_ratings_count > 0
        else 0.0
    )
    total_questions = total_pending_q + total_answered_q
    response_rate = (
        round((total_answered_q / total_questions) * 100.0, 2)
        if total_questions > 0
        else 100.0
    )

    return TeacherAnalyticsResponse(
        teacher_id=user.id,
        period=period,
        course_id=course_id,
        enrollments=MetricIndicator(
            value=total_enrollments,
            source="EnrollmentAccessService (matrículas confirmadas)",
            description="Total de alunos matriculados no período selecionado",
        ),
        active_students=MetricIndicator(
            value=total_active,
            source="ProgressService (atividade de reprodução)",
            description="Alunos com visualização registrada no período",
        ),
        completion_rate=MetricIndicator(
            value=overall_completion,
            source="ProgressService (conclusão de aulas)",
            description="Percentual médio de conclusão dos cursos do professor",
        ),
        average_rating=MetricIndicator(
            value=overall_rating,
            source="LessonInteractionService / ContentRating (banco de dados)",
            description="Média das avaliações (1 a 5 estrelas) de aulas e cursos",
        ),
        total_ratings=MetricIndicator(
            value=total_ratings_count,
            source="LessonInteractionService / ContentRating (banco de dados)",
            description="Quantidade total de avaliações recebidas",
        ),
        question_response_rate=MetricIndicator(
            value=response_rate,
            source="QuestionService / Question (banco de dados)",
            description="Percentual de dúvidas respondidas pelo professor",
        ),
        courses=course_items,
    )
