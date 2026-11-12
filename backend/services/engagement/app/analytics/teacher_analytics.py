"""TeacherAnalyticsService implementation (F26, F41)."""

from datetime import datetime, timedelta, timezone
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
from app.library_interaction.models import ContentRating, LessonHistory
from app.permissions import require_course_access, require_teacher

PERIOD_DAYS = {"30d": 30, "90d": 90, "365d": 365}
NOT_INTEGRATED = " — não integrado: indicador indisponível"


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
    session: Session, course_id: str, lesson_ids: list[str], since: datetime
) -> tuple[float, int]:
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
        ).where(or_(*conditions), ContentRating.updated_at >= since)
    ).one()
    avg_stars = round(float(row[0]), 2) if row[0] is not None else 0.0
    total = int(row[1] or 0)
    return avg_stars, total


def _question_count(session: Session, course_id: str, status: str, since: datetime) -> int:
    return int(
        session.scalar(
            select(func.count(Question.id)).where(
                Question.course_id == course_id,
                Question.status == status,
                Question.created_at >= since,
            )
        )
        or 0
    )


def _active_students(session: Session, lesson_ids: list[str], since: datetime) -> set[str]:
    """Distinct students who opened a lesson of the course in the period (F21 history)."""
    if not lesson_ids:
        return set()
    return set(
        session.scalars(
            select(LessonHistory.student_id)
            .where(
                LessonHistory.lesson_id.in_(lesson_ids),
                LessonHistory.viewed_at >= since,
            )
            .distinct()
        )
    )


def obter_indicadores_professor(
    session: Session,
    integrations: Integrations,
    user: User,
    period: Literal["30d", "90d", "365d"] = "30d",
    course_id: str | None = None,
) -> TeacherAnalyticsResponse:
    """F41 — Validar propriedade dos cursos do professor e consolidar métricas com origem dos indicadores."""
    require_teacher(user)
    since = datetime.now(timezone.utc) - timedelta(days=PERIOD_DAYS[period])

    if course_id is not None:
        course = require_course_access(user, integrations, course_id, write=True)
        teacher_courses: list[Course] = [course]
    else:
        teacher_courses = [
            c for c in integrations.courses() if c.owner_id == user.id
        ]

    course_items: list[CourseAnalyticsItem] = []
    enrollment_values: list[int | None] = []
    weighted_completion: list[tuple[float, int]] = []
    completion_available = True
    active_from_owner = True
    active_owner_total = 0
    active_local: set[str] = set()
    weighted_rating_sum = 0.0
    total_ratings_count = 0
    total_pending_q = 0
    total_answered_q = 0

    for course in teacher_courses:
        snapshot = integrations.course_engagement_snapshot(course.id, period)
        lesson_ids = [lesson.id for lesson in integrations.course_lessons(course.id)]
        avg_rating, rating_count = _course_ratings_summary(
            session, course.id, lesson_ids, since
        )
        pending_q = _question_count(session, course.id, "pending", since)
        answered_q = _question_count(session, course.id, "answered", since)

        enrollments = snapshot.get("enrollments")
        enrollments = int(enrollments) if enrollments is not None else None
        completion_rate = snapshot.get("completion_rate")
        completion_rate = float(completion_rate) if completion_rate is not None else None
        watch = snapshot.get("avg_watch_minutes")
        watch = int(watch) if watch is not None else None

        owner_active = snapshot.get("active_students")
        if owner_active is not None:
            active_students = int(owner_active)
            active_owner_total += active_students
        else:
            active_from_owner = False
            students = _active_students(session, lesson_ids, since)
            active_local |= students
            active_students = len(students)

        enrollment_values.append(enrollments)
        if completion_rate is None or enrollments is None:
            completion_available = False
        elif enrollments > 0:
            weighted_completion.append((completion_rate, enrollments))
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
                avg_watch_minutes=watch,
                average_rating=avg_rating,
                total_ratings=rating_count,
                pending_questions=pending_q,
                answered_questions=answered_q,
            )
        )

    enrollments_available = all(value is not None for value in enrollment_values)
    total_enrollments = (
        sum(value or 0 for value in enrollment_values) if enrollments_available else None
    )
    # Weighted by enrollments: an empty course must not pull the average down.
    enrolled = sum(weight for _, weight in weighted_completion)
    overall_completion = (
        round(sum(rate * weight for rate, weight in weighted_completion) / enrolled, 2)
        if completion_available and enrolled > 0
        else (0.0 if completion_available else None)
    )
    if teacher_courses and not active_from_owner:
        # Students are counted once even when active in several courses.
        total_active = active_owner_total + len(active_local)
        active_source = "StudyLibraryService / LessonHistory (banco de dados)"
        active_description = "Alunos distintos que abriram aulas no período selecionado"
    else:
        total_active = active_owner_total
        active_source = "ProgressService (atividade de reprodução)"
        active_description = "Alunos com visualização registrada no período"
    overall_rating = (
        round(weighted_rating_sum / total_ratings_count, 2)
        if total_ratings_count > 0
        else 0.0
    )
    total_questions = total_pending_q + total_answered_q
    response_rate = (
        round((total_answered_q / total_questions) * 100.0, 2)
        if total_questions > 0
        else None
    )

    return TeacherAnalyticsResponse(
        teacher_id=user.id,
        period=period,
        course_id=teacher_courses[0].id if course_id is not None else None,
        enrollments=MetricIndicator(
            value=total_enrollments,
            source="EnrollmentAccessService (matrículas confirmadas)"
            + ("" if total_enrollments is not None else NOT_INTEGRATED),
            description="Total de alunos matriculados no período selecionado",
        ),
        active_students=MetricIndicator(
            value=total_active,
            source=active_source,
            description=active_description,
        ),
        completion_rate=MetricIndicator(
            value=overall_completion,
            source="ProgressService (conclusão de aulas)"
            + ("" if overall_completion is not None else NOT_INTEGRATED),
            description="Percentual de conclusão ponderado pelas matrículas de cada curso",
        ),
        average_rating=MetricIndicator(
            value=overall_rating,
            source="LessonInteractionService / ContentRating (banco de dados)",
            description="Média das avaliações (1 a 5 estrelas) de aulas e cursos no período",
        ),
        total_ratings=MetricIndicator(
            value=total_ratings_count,
            source="LessonInteractionService / ContentRating (banco de dados)",
            description="Quantidade de avaliações registradas ou atualizadas no período",
        ),
        question_response_rate=MetricIndicator(
            value=response_rate,
            source="QuestionService / Question (banco de dados)",
            description="Percentual respondido das dúvidas recebidas no período"
            + ("" if response_rate is not None else " (nenhuma dúvida no período)"),
        ),
        courses=course_items,
    )
