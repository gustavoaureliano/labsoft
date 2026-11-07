"""ReportController and ContentModerationController HTTP routes (F28, F45)."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_session
from app.integrations import Integrations, User, get_current_user, get_integrations
from app.moderation import content_moderation as moderation_service
from app.moderation import reports as report_service
from app.moderation.schemas import (
    ModerationDecisionRequest,
    ModerationDecisionResponse,
    ModerationQueueItemResponse,
    MyReportStatusResponse,
    ReportCreateRequest,
    ReportResponse,
)

router = APIRouter(prefix="/api/moderation", tags=["Moderação"])


@router.get(
    "/reports/my/{item_type}/{item_id}",
    response_model=MyReportStatusResponse,
)
def consultar_minha_denuncia(
    item_type: Literal["lesson", "course", "comment"],
    item_id: str,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> MyReportStatusResponse:
    """Consultar status de denúncia do usuário autenticado para um item."""
    return report_service.consultar_status_denuncia_usuario(
        session, user, item_type, item_id
    )


@router.post("/reports", response_model=ReportResponse, status_code=201)
def enviar_denuncia(
    data: ReportCreateRequest,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> ReportResponse:
    """F28 — Denunciar aula, curso ou comentário."""
    try:
        return report_service.registrar_denuncia(
            session,
            integrations,
            user,
            data.item_id,
            data.item_type,
            data.reason,
        )
    except report_service.ReportedTargetNotFound as exc:
        raise HTTPException(404, str(exc)) from exc
    except report_service.DuplicateReportError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get("/queue", response_model=list[ModerationQueueItemResponse])
def listar_denuncias_pendentes(
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> list[ModerationQueueItemResponse]:
    """F45 — Listar fila de moderação pendente."""
    return moderation_service.obter_fila_pendente(session, integrations, user)


@router.post(
    "/queue/{item_id}/decision", response_model=ModerationDecisionResponse
)
def moderar_item(
    item_id: str,
    data: ModerationDecisionRequest,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> ModerationDecisionResponse:
    """F45 — Aplicar decisão de moderação (manter, ocultar ou excluir) e registrar auditoria."""
    try:
        return moderation_service.aplicar_decisao(
            session,
            integrations,
            user,
            item_id,
            data.item_type,
            data.decision,
            data.justification,
        )
    except moderation_service.ModerationItemNotFound as exc:
        raise HTTPException(404, str(exc)) from exc
