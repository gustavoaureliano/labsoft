"""ReportService implementation (F28, F45)."""

from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import commit_with_retry
from app.integrations import Integrations, User
from app.library_interaction.models import LessonComment
from app.moderation import content_moderation as moderation_service
from app.moderation.models import ContentReport, ModerationQueueItem
from app.moderation.schemas import (
    ModerationQueueItemResponse,
    MyReportStatusResponse,
    ReportResponse,
)
from app.permissions import canonical_id, require_lesson_access


class DuplicateReportError(Exception):
    pass


class ReportedTargetNotFound(Exception):
    pass


def _resolve_target_metadata(
    session: Session,
    integrations: Integrations,
    item_type: Literal["lesson", "course", "comment"],
    item_id: str,
) -> tuple[str, str]:
    if item_type == "lesson":
        lesson = integrations.lesson(item_id)
        if lesson is None:
            raise ReportedTargetNotFound("Aula denunciada não encontrada")
        course = integrations.course(lesson.course_id)
        return lesson.title, (course.teacher if course else lesson.course_id)
    if item_type == "course":
        course = integrations.course(item_id)
        if course is None:
            raise ReportedTargetNotFound("Curso denunciado não encontrado")
        return course.title, course.teacher
    comment = session.get(LessonComment, item_id)
    if comment is None:
        raise ReportedTargetNotFound("Comentário denunciado não encontrado")
    return comment.content, comment.author_name


def _reportable_item_id(
    session: Session,
    integrations: Integrations,
    user: User,
    item_type: Literal["lesson", "course", "comment"],
    item_id: str,
) -> str:
    """Return the canonical id of an item the user may report, or raise not found."""
    if item_type == "lesson":
        lesson = integrations.lesson(item_id)
        if lesson is None:
            raise ReportedTargetNotFound("Aula denunciada não encontrada")
        return lesson.id
    if item_type == "course":
        course = integrations.course(item_id)
        if course is None:
            raise ReportedTargetNotFound("Curso denunciado não encontrado")
        return course.id
    comment = session.get(LessonComment, canonical_id(item_id))
    # Only publicly visible comments can be reported: hidden/deleted ones were
    # already moderated and held ones are already waiting in the queue.
    if comment is None or comment.moderation_status != "approved":
        raise ReportedTargetNotFound("Comentário denunciado não encontrado")
    require_lesson_access(user, integrations, comment.lesson_id)
    return comment.id


def registrar_denuncia(
    session: Session,
    integrations: Integrations,
    user: User,
    item_id: str,
    item_type: Literal["lesson", "course", "comment"],
    reason: str,
) -> ReportResponse:
    """F28 — Verificar duplicidade, salvar denúncia e enfileirar item para moderação."""
    item_id = _reportable_item_id(session, integrations, user, item_type, item_id)

    def stage() -> ContentReport:
        existing = session.scalar(
            select(ContentReport).where(
                ContentReport.reporter_id == user.id,
                ContentReport.item_type == item_type,
                ContentReport.item_id == item_id,
            )
        )
        if existing is not None:
            raise DuplicateReportError("Você já enviou uma denúncia para este item")

        report = ContentReport(
            reporter_id=user.id,
            item_type=item_type,
            item_id=item_id,
            reason=reason,
            status="pending",
        )
        session.add(report)
        session.flush()
        moderation_service.enfileirar_item_para_moderacao(session, item_id, item_type)
        return report

    report = commit_with_retry(session, stage)
    session.refresh(report)
    return ReportResponse.model_validate(report)


def consultar_status_denuncia_usuario(
    session: Session,
    user: User,
    item_type: Literal["lesson", "course", "comment"],
    item_id: str,
) -> MyReportStatusResponse:
    """Consulta no banco se o usuário já denunciou o item e qual foi a decisão da moderação."""
    item_id = canonical_id(item_id)
    report = session.scalar(
        select(ContentReport).where(
            ContentReport.reporter_id == user.id,
            ContentReport.item_type == item_type,
            ContentReport.item_id == item_id,
        )
    )
    if report is None:
        return MyReportStatusResponse(reported=False)

    queue_item = session.scalar(
        select(ModerationQueueItem).where(
            ModerationQueueItem.item_type == item_type,
            ModerationQueueItem.item_id == item_id,
        )
    )
    decision_label: Literal["mantido", "ocultado", "excluído"] | None = None
    if queue_item is not None and queue_item.status != "pending":
        label_map: dict[str, Literal["mantido", "ocultado", "excluído"]] = {
            "kept": "mantido",
            "hidden": "ocultado",
            "deleted": "excluído",
        }
        decision_label = label_map.get(queue_item.status)

    return MyReportStatusResponse(
        reported=True,
        reason=report.reason,
        status=report.status,  # type: ignore[arg-type]
        decision=decision_label,
    )


def consultar_denuncias_pendentes(
    session: Session, integrations: Integrations
) -> list[ModerationQueueItemResponse]:
    """F45 — Consultar denúncias pendentes, conteúdo, autor e motivos para a fila de moderação."""
    queue_items = session.scalars(
        select(ModerationQueueItem)
        .where(ModerationQueueItem.status == "pending")
        .order_by(ModerationQueueItem.created_at.desc())
    )
    result: list[ModerationQueueItemResponse] = []
    for queue_item in queue_items:
        reports = list(
            session.scalars(
                select(ContentReport).where(
                    ContentReport.item_type == queue_item.item_type,
                    ContentReport.item_id == queue_item.item_id,
                    ContentReport.status == "pending",
                )
            )
        )
        try:
            title_or_excerpt, author_or_owner = _resolve_target_metadata(
                session,
                integrations,
                queue_item.item_type,  # type: ignore[arg-type]
                queue_item.item_id,
            )
        except ReportedTargetNotFound:
            title_or_excerpt, author_or_owner = queue_item.item_id, "Desconhecido"

        reasons = [r.reason for r in reports] or ["Revisão administrativa pendente"]
        result.append(
            ModerationQueueItemResponse(
                queue_id=queue_item.id,
                item_type=queue_item.item_type,  # type: ignore[arg-type]
                item_id=queue_item.item_id,
                title_or_excerpt=title_or_excerpt,
                author_or_owner=author_or_owner,
                reasons=reasons,
                reports_count=len(reports),
                status=queue_item.status,  # type: ignore[arg-type]
                created_at=queue_item.created_at,
            )
        )
    return result
