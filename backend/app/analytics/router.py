"""TeacherAnalyticsController and AdminDashboardController HTTP routes (F41, F43)."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.analytics import admin_dashboard as admin_dashboard_service
from app.analytics import teacher_analytics as teacher_analytics_service
from app.analytics.schemas import AdminDashboardResponse, TeacherAnalyticsResponse
from app.database import get_session
from app.integrations import Integrations, User, get_current_user, get_integrations

router = APIRouter(prefix="/api/analytics", tags=["Análise e Indicadores"])


@router.get("/teacher", response_model=TeacherAnalyticsResponse)
def consultar_metricas_professor(
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
    period: Annotated[Literal["30d", "90d", "365d"], Query()] = "30d",
    course_id: Annotated[str | None, Query()] = None,
) -> TeacherAnalyticsResponse:
    """F41 — Consultar métricas do professor filtradas por período e curso."""
    return teacher_analytics_service.obter_indicadores_professor(
        session, integrations, user, period=period, course_id=course_id
    )


@router.get("/admin-dashboard", response_model=AdminDashboardResponse)
def consultar_dashboard_admin(
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
    period: Annotated[Literal["monthly", "annual"], Query()] = "monthly",
) -> AdminDashboardResponse:
    """F43 — Consultar dashboard administrativo (mensal ou anual)."""
    return admin_dashboard_service.carregar_indicadores_plataforma(
        session, integrations, user, period=period
    )
