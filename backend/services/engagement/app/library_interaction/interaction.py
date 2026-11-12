"""LessonInteractionService implementation (F24, F25, F26)."""

from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics import teacher_analytics as analytics_service
from app.communication import notifications as notification_service
from app.database import commit_with_retry
from app.integrations import Integrations, User
from app.library_interaction.models import (
    ContentRating,
    LessonComment,
    PrivateNote,
)
from app.library_interaction.schemas import (
    CommentResponse,
    PrivateNoteResponse,
    RatingSummaryResponse,
)
from app.moderation import content_moderation as moderation_service
from app.permissions import (
    canonical_id,
    require_course_access,
    require_lesson_access,
    require_student,
)


class ParentCommentNotFound(Exception):
    pass


def _canonical_target(
    user: User,
    integrations: Integrations,
    target_type: Literal["lesson", "course"],
    target_id: str,
) -> str:
    """Check access and return the id spelled exactly as its owner service stores it."""
    if target_type == "lesson":
        return require_lesson_access(user, integrations, target_id).id
    return require_course_access(user, integrations, target_id).id


def obter_anotacao_do_proprietario(
    session: Session, integrations: Integrations, user: User, lesson_id: str
) -> PrivateNoteResponse:
    """F24 — Consultar anotação privada restrita ao alunoId e aulaId."""
    require_student(user)
    lesson_id = require_lesson_access(user, integrations, lesson_id).id
    note = session.get(PrivateNote, (user.id, lesson_id))
    if note is None:
        return PrivateNoteResponse(
            student_id=user.id,
            lesson_id=lesson_id,
            content="",
            updated_at=None,
        )
    return PrivateNoteResponse(
        student_id=note.student_id,
        lesson_id=note.lesson_id,
        content=note.content,
        updated_at=note.updated_at,
    )


def salvar_anotacao_privada(
    session: Session,
    integrations: Integrations,
    user: User,
    lesson_id: str,
    content: str,
) -> PrivateNoteResponse:
    """F24 — Inserir ou atualizar anotação privada vinculada ao aluno e à aula.

    Conteúdo vazio apaga a anotação.
    """
    require_student(user)
    lesson_id = require_lesson_access(user, integrations, lesson_id).id
    now = datetime.now(timezone.utc)
    if not content:
        existing = session.get(PrivateNote, (user.id, lesson_id))
        if existing is not None:
            session.delete(existing)
            session.commit()
        return PrivateNoteResponse(
            student_id=user.id, lesson_id=lesson_id, content="", updated_at=None
        )

    def stage() -> PrivateNote:
        note = session.get(PrivateNote, (user.id, lesson_id))
        if note is None:
            note = PrivateNote(
                student_id=user.id,
                lesson_id=lesson_id,
                content=content,
                updated_at=now,
            )
            session.add(note)
        else:
            note.content = content
            note.updated_at = now
        return note

    note = commit_with_retry(session, stage)
    session.refresh(note)
    return PrivateNoteResponse(
        student_id=note.student_id,
        lesson_id=note.lesson_id,
        content=note.content,
        updated_at=note.updated_at,
    )


def publicar_comentario(
    session: Session,
    integrations: Integrations,
    user: User,
    lesson_id: str,
    content: str,
    parent_id: str | None = None,
) -> CommentResponse:
    """F25 — Verificar estado de moderação, salvar comentário e notificar autor original em respostas aprovadas."""
    lesson_id = require_lesson_access(user, integrations, lesson_id).id

    parent_comment: LessonComment | None = None
    if parent_id is not None:
        parent_comment = session.get(LessonComment, canonical_id(parent_id))
        # Hidden, deleted or held comments must not receive replies (nor notify
        # their authors): they are not visible to the public.
        if (
            parent_comment is None
            or parent_comment.lesson_id != lesson_id
            or parent_comment.moderation_status != "approved"
        ):
            raise ParentCommentNotFound("Comentário original não encontrado nesta aula")
        parent_id = parent_comment.id

    moderation_state = moderation_service.verificar_estado_moderacao(content)

    comment = LessonComment(
        lesson_id=lesson_id,
        author_id=user.id,
        author_name=user.name,
        parent_id=parent_id,
        content=content,
        moderation_status=moderation_state,
    )
    session.add(comment)
    session.flush()

    if moderation_state == "held":
        moderation_service.enfileirar_item_para_moderacao(
            session, comment.id, "comment"
        )
    elif parent_comment is not None and parent_comment.author_id != user.id:
        notification_service.notificar_autor_original(
            session, parent_comment.author_id, lesson_id, user.name
        )

    session.commit()
    session.refresh(comment)
    return CommentResponse.model_validate(comment)


def listar_comentarios_aula(
    session: Session, integrations: Integrations, user: User, lesson_id: str
) -> list[CommentResponse]:
    """F25 — Listar comentários públicos aprovados da aula.

    Respostas cujo comentário original foi ocultado, excluído ou retido também
    deixam de ser exibidas, para não expor uma conversa sobre conteúdo moderado.
    """
    lesson_id = require_lesson_access(user, integrations, lesson_id).id
    rows = list(
        session.scalars(
            select(LessonComment)
            .where(
                LessonComment.lesson_id == lesson_id,
                LessonComment.moderation_status == "approved",
            )
            .order_by(LessonComment.created_at.asc(), LessonComment.id.asc())
        )
    )
    approved_ids = {row.id for row in rows}
    by_id = {row.id: row for row in rows}

    def visible(row: LessonComment) -> bool:
        seen: set[str] = set()
        while row.parent_id is not None:
            if row.parent_id not in approved_ids or row.parent_id in seen:
                return False
            seen.add(row.parent_id)
            row = by_id[row.parent_id]
        return True

    return [CommentResponse.model_validate(row) for row in rows if visible(row)]


def registrar_avaliacao(
    session: Session,
    integrations: Integrations,
    user: User,
    target_type: Literal["lesson", "course"],
    target_id: str,
    stars: int,
) -> RatingSummaryResponse:
    """F26 — Inserir ou atualizar avaliação única do aluno e recalcular média e total no TeacherAnalyticsService."""
    require_student(user)
    target_id = _canonical_target(user, integrations, target_type, target_id)
    now = datetime.now(timezone.utc)

    def stage() -> None:
        existing = session.scalar(
            select(ContentRating).where(
                ContentRating.student_id == user.id,
                ContentRating.target_type == target_type,
                ContentRating.target_id == target_id,
            )
        )
        if existing is None:
            session.add(
                ContentRating(
                    student_id=user.id,
                    target_type=target_type,
                    target_id=target_id,
                    stars=stars,
                    updated_at=now,
                )
            )
        else:
            existing.stars = stars
            existing.updated_at = now

    commit_with_retry(session, stage)
    avg_rating, total_ratings = analytics_service.recalcular_media_avaliacoes(
        session, target_type, target_id
    )

    return RatingSummaryResponse(
        target_type=target_type,
        target_id=target_id,
        student_stars=stars,
        average_rating=avg_rating,
        total_ratings=total_ratings,
    )


def consultar_avaliacao(
    session: Session,
    integrations: Integrations,
    user: User,
    target_type: Literal["lesson", "course"],
    target_id: str,
) -> RatingSummaryResponse:
    """F26 — Consultar avaliação atual do aluno e média geral do conteúdo."""
    target_id = _canonical_target(user, integrations, target_type, target_id)

    existing = session.scalar(
        select(ContentRating).where(
            ContentRating.student_id == user.id,
            ContentRating.target_type == target_type,
            ContentRating.target_id == target_id,
        )
    )
    avg_rating, total_ratings = analytics_service.recalcular_media_avaliacoes(
        session, target_type, target_id
    )
    return RatingSummaryResponse(
        target_type=target_type,
        target_id=target_id,
        student_stars=existing.stars if existing else None,
        average_rating=avg_rating,
        total_ratings=total_ratings,
    )
