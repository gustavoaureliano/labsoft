"""AdminDashboardService implementation (F43)."""

from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analytics.schemas import AccessSeriesPoint, AdminDashboardResponse
from app.integrations import Integrations, User
from app.library_interaction.models import LessonComment
from app.moderation.models import ModerationQueueItem
from app.permissions import require_admin


def carregar_indicadores_plataforma(
    session: Session,
    integrations: Integrations,
    user: User,
    period: Literal["monthly", "annual"] = "monthly",
) -> AdminDashboardResponse:
    """F43 — Consultar total de usuários, professores e cursos e série histórica de acessos por período."""
    require_admin(user)
    snapshot = integrations.platform_snapshot(period)

    pending_moderation = int(
        session.scalar(
            select(func.count(ModerationQueueItem.id)).where(
                ModerationQueueItem.status == "pending"
            )
        )
        or 0
    )
    held_comments = int(
        session.scalar(
            select(func.count(LessonComment.id)).where(
                LessonComment.moderation_status == "held"
            )
        )
        or 0
    )

    series = [
        AccessSeriesPoint(label=item["label"], count=int(item["count"]))
        for item in snapshot["access_series"]
    ]
    total_accesses = sum(point.count for point in series)

    return AdminDashboardResponse(
        period=period,
        total_users=int(snapshot["total_users"]),
        total_students=int(snapshot["total_students"]),
        total_teachers=int(snapshot["total_teachers"]),
        total_courses=int(snapshot["total_courses"]),
        total_accesses_in_period=total_accesses,
        pending_moderation_items=pending_moderation,
        held_comments_count=held_comments,
        access_series=series,
    )
