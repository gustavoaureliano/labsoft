"""ContentModerationService implementation (F25, F28, F45)."""

from datetime import datetime, timezone
import unicodedata
from uuid import UUID, uuid4
from typing import Literal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.communication import notifications as notification_service
from app.integrations import Integrations, User
from app.library_interaction.models import LessonComment
from app.moderation.models import ContentReport, ModerationQueueItem
from app.moderation.schemas import (
    ModerationDecisionResponse,
    ModerationQueueItemResponse,
)
from app.permissions import canonical_id, require_admin

BLOCKED_TERMS = {"ofensivo", "improprio", "spam", "golpe", "palavrao"}


class ModerationItemNotFound(Exception):
    pass


class ModerationAlreadyDecided(Exception):
    pass


def _strip_accents(texto: str) -> str:
    decomposed = unicodedata.normalize("NFKD", texto)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def verificar_estado_moderacao(texto: str) -> Literal["approved", "held"]:
    """F25 — Verificar se o comentário deve ser aprovado ou retido automaticamente."""
    normalized = _strip_accents(texto.lower())
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
            operation_id=str(uuid4()),
        )
        session.add(queue_item)
    else:
        if queue_item.status != "pending":
            queue_item.operation_id = str(uuid4())
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


def _decision_response(
    queue_item: ModerationQueueItem, audit_recorded: bool
) -> ModerationDecisionResponse:
    return ModerationDecisionResponse(
        queue_id=queue_item.id,
        item_type=queue_item.item_type,  # type: ignore[arg-type]
        item_id=queue_item.item_id,
        status=queue_item.status,  # type: ignore[arg-type]
        decision=queue_item.decision,  # type: ignore[arg-type]
        admin_id=queue_item.admin_id or "",
        justification=queue_item.justification or "",
        decided_at=queue_item.decided_at or datetime.now(timezone.utc),
        audit_recorded=audit_recorded,
    )


def aplicar_decisao(
    session: Session,
    integrations: Integrations,
    user: User,
    item_id: str,
    item_type: Literal["lesson", "course", "comment"],
    decision: Literal["keep", "hide", "delete"],
    justification: str,
) -> ModerationDecisionResponse:
    """F45 — Aplicar decisão (manter, ocultar ou excluir), encerrar denúncias e registrar trilha de auditoria.

    A linha da fila fica travada durante toda a operação, então duas decisões
    simultâneas são serializadas. Repetir a decisão atual é idempotente; uma
    decisão diferente revisa a anterior (exceto exclusão, que é definitiva).
    """
    require_admin(user)
    item_id = canonical_id(item_id)
    queue_item = session.scalar(
        select(ModerationQueueItem)
        .where(
            ModerationQueueItem.item_type == item_type,
            ModerationQueueItem.item_id == item_id,
        )
        .with_for_update()
    )
    if queue_item is None:
        raise ModerationItemNotFound("Item não encontrado na fila de moderação")
    if queue_item.status != "pending":
        if queue_item.decision == decision:
            # Repeating the current decision (e.g. a retry after a lost
            # response) changes nothing and records no second audit entry.
            session.rollback()
            return _decision_response(queue_item, audit_recorded=True)
        if queue_item.status == "deleted":
            # Deletion is irreversible, as in the catalog and learning owners.
            session.rollback()
            raise ModerationAlreadyDecided("Item excluído não pode ter a decisão alterada")
        # Revising a decision (e.g. restoring hidden content) is a new audited
        # operation. Its id is only persisted together with the outcome, so a
        # failure leaves the previous decision intact instead of a pending case.
        queue_item.operation_id = str(uuid4())
    if not queue_item.operation_id:
        # Legacy rows: reuse the queue id when it is a UUID (identity requires one).
        try:
            queue_item.operation_id = str(UUID(queue_item.id))
        except ValueError:
            queue_item.operation_id = str(uuid4())

    comment: LessonComment | None = None
    previous_comment_status: str | None = None
    if item_type == "comment":
        comment = session.get(LessonComment, item_id)
        if comment is None:
            session.rollback()
            raise ModerationItemNotFound("Comentário não encontrado")
        previous_comment_status = comment.moderation_status
    else:
        # The owner service (catalog/learning) applies the decision first; if the
        # audit below fails, the case stays pending and a retry repeats both
        # idempotent commands with the same operation_id.
        integrations.apply_moderation(item_type, item_id, decision)

    status_map: dict[str, Literal["kept", "hidden", "deleted"]] = {
        "keep": "kept",
        "hide": "hidden",
        "delete": "deleted",
    }
    new_status = status_map[decision]

    if comment is not None:
        comment.moderation_status = {
            "keep": "approved",
            "hide": "hidden",
            "delete": "deleted",
        }[decision]
        if decision == "keep" and previous_comment_status == "held" and comment.parent_id:
            # A held reply that is approved now reaches the original author (F25).
            parent = session.get(LessonComment, comment.parent_id)
            if (
                parent is not None
                and parent.moderation_status == "approved"
                and parent.author_id != comment.author_id
            ):
                notification_service.notificar_autor_original(
                    session, parent.author_id, comment.lesson_id, comment.author_name
                )

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

    try:
        integrations.record_audit(
            admin_id=user.id,
            item_id=item_id,
            item_type=item_type,
            decision=decision,
            justification=justification,
            operation_id=queue_item.operation_id,
        )
    except HTTPException as exc:
        if exc.status_code != 409:
            raise
        # An earlier attempt that failed here locally was already audited with a
        # different payload under this operation_id. The owner now holds this
        # decision, so it is recorded as a new audited operation.
        queue_item.operation_id = str(uuid4())
        integrations.record_audit(
            admin_id=user.id,
            item_id=item_id,
            item_type=item_type,
            decision=decision,
            justification=justification,
            operation_id=queue_item.operation_id,
        )

    session.commit()
    session.refresh(queue_item)
    return _decision_response(queue_item, audit_recorded=True)
