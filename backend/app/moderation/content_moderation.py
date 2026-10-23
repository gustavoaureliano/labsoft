"""ContentModerationService implementation (F25, F28, F45)."""

from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations import Integrations, User
from app.library_interaction.models import LessonComment
from app.moderation.models import ContentReport, ModerationQueueItem
from app.moderation.schemas import (
    ModerationDecisionResponse,
    ModerationQueueItemResponse,
)
from app.permissions import require_admin

BLOCKED_TERMS = {"ofensivo", "improprio", "spam", "golpe", "palavrao"}


class ModerationItemNotFound(Exception):
    pass


def verificar_estado_moderacao(texto: str) -> Literal["approved", "held"]:
    """F25 — Verificar se o comentário deve ser aprovado ou retido automaticamente."""
    normalized = texto.lower()
    if any(term in normalized for term in BLOCKED_TERMS):
        return "held"
    return "approved"


def enfileirar_item_para_moderacao(
    session: Session, item_id: str, item_type: Literal["lesson", "course", "comment"]
) -> ModerationQueueItem:
    """F28 — Incluir ou reabrir item na fila de moderação pendente."""
    queue_item = session.scalar(
        select(ModerationQueueItem).where(
            ModerationQueueItem.item_type == item_type,
            ModerationQueueItem.item_id == item_id,
        )
    )
    if queue_item is None:
        queue_item = ModerationQueueItem(
            item_type=item_type,
            item_id=item_id,
            status="pending",
        )
        session.add(queue_item)
    else:
        queue_item.status = "pending"
        queue_item.decision = None
        queue_item.admin_id = None
        queue_item.justification = None
        queue_item.decided_at = None
    session.flush()
    return queue_item


def obter_fila_pendente(
    session: Session, integrations: Integrations, user: User
) -> list[ModerationQueueItemResponse]:
    """F45 — Obter fila de moderação pendente consultando ReportService."""
    require_admin(user)
    from app.moderation import reports as report_service

    return report_service.consultar_denuncias_pendentes(session, integrations)


def aplicar_decisao(
    session: Session,
    integrations: Integrations,
    user: User,
    item_id: str,
    item_type: Literal["lesson", "course", "comment"],
    decision: Literal["keep", "hide", "delete"],
    justification: str,
) -> ModerationDecisionResponse:
    """F45 — Aplicar decisão (manter, ocultar ou excluir), encerrar denúncias e registrar trilha de auditoria."""
    require_admin(user)
    queue_item = session.scalar(
        select(ModerationQueueItem).where(
            ModerationQueueItem.item_type == item_type,
            ModerationQueueItem.item_id == item_id,
        )
    )
    if queue_item is None:
        raise ModerationItemNotFound("Item não encontrado na fila de moderação")

    status_map: dict[str, Literal["kept", "hidden", "deleted"]] = {
        "keep": "kept",
        "hide": "hidden",
        "delete": "deleted",
    }
    new_status = status_map[decision]

    if item_type == "comment":
        comment = session.get(LessonComment, item_id)
        if comment is not None:
            comment_status_map = {
                "keep": "approved",
                "hide": "hidden",
                "delete": "deleted",
            }
            comment.moderation_status = comment_status_map[decision]

    now = datetime.now(timezone.utc)
    queue_item.status = new_status
    queue_item.decision = decision
    queue_item.admin_id = user.id
    queue_item.justification = justification
    queue_item.decided_at = now

    pending_reports = session.scalars(
        select(ContentReport).where(
            ContentReport.item_type == item_type,
            ContentReport.item_id == item_id,
            ContentReport.status == "pending",
        )
    )
    for report in pending_reports:
        report.status = "resolved"

    audit_entry = integrations.record_audit(
        admin_id=user.id,
        item_id=item_id,
        item_type=item_type,
        decision=decision,
        justification=justification,
    )

    session.commit()
    session.refresh(queue_item)

    return ModerationDecisionResponse(
        queue_id=queue_item.id,
        item_type=item_type,
        item_id=item_id,
        status=new_status,
        decision=decision,
        admin_id=user.id,
        justification=justification,
        decided_at=queue_item.decided_at or now,
        audit_recorded=bool(audit_entry),
    )
