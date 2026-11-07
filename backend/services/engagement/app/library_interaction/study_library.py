"""StudyLibraryService implementation (F21, F22, F23)."""

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.integrations import Integrations, User
from app.library_interaction.models import (
    LessonFavorite,
    LessonHistory,
    Playlist,
    PlaylistItem,
)
from app.library_interaction.schemas import (
    FavoriteEntryResponse,
    HistoryEntryResponse,
    PlaylistPlaybackContextResponse,
    PlaylistResponse,
)
from app.permissions import require_lesson_access, require_student


class PlaylistNotFound(Exception):
    pass


class PlaylistConflict(Exception):
    pass


class PlaylistLessonNotFound(Exception):
    pass


def registrar_aula_assistida(
    session: Session, integrations: Integrations, user: User, lesson_id: str
) -> HistoryEntryResponse:
    """F21 — Salvar ou atualizar data de visualização da aula."""
    require_student(user)
    lesson = require_lesson_access(user, integrations, lesson_id)
    now = datetime.now(timezone.utc)

    record = session.get(LessonHistory, (user.id, lesson_id))
    if record is None:
        record = LessonHistory(
            student_id=user.id, lesson_id=lesson_id, viewed_at=now
        )
        session.add(record)
    else:
        record.viewed_at = now
    session.commit()
    session.refresh(record)
    return HistoryEntryResponse(
        lesson_id=record.lesson_id,
        title=lesson.title,
        course_id=lesson.course_id,
        viewed_at=record.viewed_at,
    )


def listar_historico_recente(
    session: Session, integrations: Integrations, user: User
) -> list[HistoryEntryResponse]:
    """F21 — Consultar aulas ordenadas pelas visualizações mais recentes."""
    require_student(user)
    rows = session.scalars(
        select(LessonHistory)
        .where(LessonHistory.student_id == user.id)
        .order_by(LessonHistory.viewed_at.desc())
    )
    items: list[HistoryEntryResponse] = []
    for row in rows:
        lesson = integrations.lesson(row.lesson_id)
        items.append(
            HistoryEntryResponse(
                lesson_id=row.lesson_id,
                title=lesson.title if lesson else row.lesson_id,
                course_id=lesson.course_id if lesson else "",
                viewed_at=row.viewed_at,
            )
        )
    return items


def adicionar_favorito(
    session: Session, integrations: Integrations, user: User, lesson_id: str
) -> FavoriteEntryResponse:
    """F22 — Verificar se a aula já está favoritada (sem duplicidade) e inserir nos favoritos do aluno."""
    require_student(user)
    lesson = require_lesson_access(user, integrations, lesson_id)

    record = session.get(LessonFavorite, (user.id, lesson_id))
    if record is None:
        record = LessonFavorite(student_id=user.id, lesson_id=lesson_id)
        session.add(record)
        session.commit()
        session.refresh(record)
    return FavoriteEntryResponse(
        lesson_id=record.lesson_id,
        title=lesson.title,
        course_id=lesson.course_id,
        created_at=record.created_at,
    )


def remover_favorito(session: Session, user: User, lesson_id: str) -> None:
    """F22 — Remover vínculo de favorito."""
    require_student(user)
    record = session.get(LessonFavorite, (user.id, lesson_id))
    if record is not None:
        session.delete(record)
        session.commit()


def listar_favoritos(
    session: Session, integrations: Integrations, user: User
) -> list[FavoriteEntryResponse]:
    """F22 — Consultar favoritos do aluno autenticado."""
    require_student(user)
    rows = session.scalars(
        select(LessonFavorite)
        .where(LessonFavorite.student_id == user.id)
        .order_by(LessonFavorite.created_at.desc())
    )
    items: list[FavoriteEntryResponse] = []
    for row in rows:
        lesson = integrations.lesson(row.lesson_id)
        items.append(
            FavoriteEntryResponse(
                lesson_id=row.lesson_id,
                title=lesson.title if lesson else row.lesson_id,
                course_id=lesson.course_id if lesson else "",
                created_at=row.created_at,
            )
        )
    return items


def _serialize_playlist(session: Session, playlist: Playlist) -> PlaylistResponse:
    lesson_ids = list(
        session.scalars(
            select(PlaylistItem.lesson_id)
            .where(PlaylistItem.playlist_id == playlist.id)
            .order_by(PlaylistItem.position.asc())
        )
    )
    return PlaylistResponse(
        id=playlist.id,
        name=playlist.name,
        lesson_ids=lesson_ids,
        created_at=playlist.created_at,
        updated_at=playlist.updated_at,
    )


def _get_owned_playlist(
    session: Session, student_id: str, playlist_id: str
) -> Playlist:
    playlist = session.get(Playlist, playlist_id)
    if playlist is None or playlist.student_id != student_id:
        raise PlaylistNotFound("Playlist não encontrada")
    return playlist


def listar_playlists(session: Session, user: User) -> list[PlaylistResponse]:
    """F23 — Listar playlists privadas do aluno."""
    require_student(user)
    rows = list(
        session.scalars(
            select(Playlist)
            .where(Playlist.student_id == user.id)
            .order_by(Playlist.created_at.asc())
        )
    )
    return [_serialize_playlist(session, row) for row in rows]


def criar_playlist(
    session: Session, user: User, name: str
) -> PlaylistResponse:
    """F23 — atualizarCadastroPlaylist (criar playlist privada)."""
    require_student(user)
    playlist = Playlist(student_id=user.id, name=name)
    session.add(playlist)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise PlaylistConflict("Já existe uma playlist com este nome") from exc
    session.refresh(playlist)
    return _serialize_playlist(session, playlist)


def renomear_playlist(
    session: Session, user: User, playlist_id: str, name: str
) -> PlaylistResponse:
    """F23 — atualizarCadastroPlaylist (renomear playlist privada)."""
    require_student(user)
    playlist = _get_owned_playlist(session, user.id, playlist_id)
    playlist.name = name
    playlist.updated_at = datetime.now(timezone.utc)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise PlaylistConflict("Já existe uma playlist com este nome") from exc
    session.refresh(playlist)
    return _serialize_playlist(session, playlist)


def excluir_playlist(
    session: Session, user: User, playlist_id: str
) -> None:
    """F23 — atualizarCadastroPlaylist (excluir playlist privada)."""
    require_student(user)
    playlist = _get_owned_playlist(session, user.id, playlist_id)
    session.execute(
        delete(PlaylistItem).where(PlaylistItem.playlist_id == playlist.id)
    )
    session.delete(playlist)
    session.commit()


def organizar_aulas_da_playlist(
    session: Session,
    integrations: Integrations,
    user: User,
    playlist_id: str,
    lesson_ids: list[str],
) -> PlaylistResponse:
    """F23 — organizarAulasDaPlaylist (adicionar, remover ou reordenar aulas na playlist)."""
    require_student(user)
    playlist = _get_owned_playlist(session, user.id, playlist_id)
    if len(lesson_ids) != len(set(lesson_ids)):
        raise PlaylistConflict("A playlist não pode conter aulas duplicadas")

    for lesson_id in lesson_ids:
        require_lesson_access(user, integrations, lesson_id)

    session.execute(
        delete(PlaylistItem).where(PlaylistItem.playlist_id == playlist.id)
    )
    session.flush()

    for index, lesson_id in enumerate(lesson_ids, start=1):
        session.add(
            PlaylistItem(
                playlist_id=playlist.id,
                lesson_id=lesson_id,
                position=index,
            )
        )
    playlist.updated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(playlist)
    return _serialize_playlist(session, playlist)


def obter_contexto_playlist(
    session: Session,
    integrations: Integrations,
    user: User,
    playlist_id: str,
    lesson_id: str,
) -> PlaylistPlaybackContextResponse:
    """F23 — obterContextoPlaylist + LessonPlaybackService.carregarAulaNoContexto."""
    require_student(user)
    playlist = _get_owned_playlist(session, user.id, playlist_id)
    sequence = list(
        session.scalars(
            select(PlaylistItem.lesson_id)
            .where(PlaylistItem.playlist_id == playlist.id)
            .order_by(PlaylistItem.position.asc())
        )
    )
    if lesson_id not in sequence:
        raise PlaylistLessonNotFound("Esta aula não faz parte da playlist")

    require_lesson_access(user, integrations, lesson_id)
    playback_data = integrations.load_lesson_in_context(lesson_id, sequence)
    return PlaylistPlaybackContextResponse(
        playlist_id=playlist.id,
        playlist_name=playlist.name,
        **playback_data,
    )
