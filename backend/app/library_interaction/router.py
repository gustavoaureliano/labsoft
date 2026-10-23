"""StudyLibraryController and LessonInteractionController HTTP routes (F21-F26)."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.database import get_session
from app.integrations import Integrations, User, get_current_user, get_integrations
from app.library_interaction import interaction as interaction_service
from app.library_interaction import study_library as library_service
from app.library_interaction.schemas import (
    CommentCreateRequest,
    CommentResponse,
    FavoriteEntryResponse,
    HistoryEntryResponse,
    PlaylistCreateRequest,
    PlaylistLessonsUpdateRequest,
    PlaylistPlaybackContextResponse,
    PlaylistRenameRequest,
    PlaylistResponse,
    PrivateNoteResponse,
    PrivateNoteUpdateRequest,
    RatingSummaryResponse,
    RatingUpdateRequest,
)

router = APIRouter(tags=["Biblioteca e Interação"])


# --- StudyLibraryController (F21, F22, F23) ---


@router.post(
    "/api/library/history/{lesson_id}",
    response_model=HistoryEntryResponse,
)
def registrar_visualizacao(
    lesson_id: str,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> HistoryEntryResponse:
    """F21 — Registrar aula aberta ou assistida no histórico."""
    return library_service.registrar_aula_assistida(
        session, integrations, user, lesson_id
    )


@router.get("/api/library/history", response_model=list[HistoryEntryResponse])
def consultar_historico(
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> list[HistoryEntryResponse]:
    """F21 — Consultar histórico de visualizações do aluno."""
    return library_service.listar_historico_recente(session, integrations, user)


@router.post(
    "/api/library/favorites/{lesson_id}",
    response_model=FavoriteEntryResponse,
    status_code=201,
)
def adicionar_favorito(
    lesson_id: str,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> FavoriteEntryResponse:
    """F22 — Adicionar aula aos favoritos."""
    return library_service.adicionar_favorito(
        session, integrations, user, lesson_id
    )


@router.delete(
    "/api/library/favorites/{lesson_id}",
    status_code=204,
    response_class=Response,
)
def remover_favorito(
    lesson_id: str,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """F22 — Remover aula dos favoritos."""
    library_service.remover_favorito(session, user, lesson_id)
    return Response(status_code=204)


@router.get(
    "/api/library/favorites", response_model=list[FavoriteEntryResponse]
)
def listar_favoritos(
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> list[FavoriteEntryResponse]:
    """F22 — Listar favoritos do aluno autenticado."""
    return library_service.listar_favoritos(session, integrations, user)


@router.get("/api/library/playlists", response_model=list[PlaylistResponse])
def listar_playlists(
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[PlaylistResponse]:
    """F23 — Listar playlists privadas do aluno."""
    return library_service.listar_playlists(session, user)


@router.post(
    "/api/library/playlists", response_model=PlaylistResponse, status_code=201
)
def criar_playlist(
    data: PlaylistCreateRequest,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> PlaylistResponse:
    """F23 — Criar playlist privada."""
    try:
        return library_service.criar_playlist(session, user, data.name)
    except library_service.PlaylistConflict as exc:
        raise HTTPException(409, str(exc)) from exc


@router.patch(
    "/api/library/playlists/{playlist_id}", response_model=PlaylistResponse
)
def renomear_playlist(
    playlist_id: str,
    data: PlaylistRenameRequest,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> PlaylistResponse:
    """F23 — Renomear playlist privada."""
    try:
        return library_service.renomear_playlist(
            session, user, playlist_id, data.name
        )
    except library_service.PlaylistNotFound as exc:
        raise HTTPException(404, str(exc)) from exc
    except library_service.PlaylistConflict as exc:
        raise HTTPException(409, str(exc)) from exc


@router.delete(
    "/api/library/playlists/{playlist_id}",
    status_code=204,
    response_class=Response,
)
def excluir_playlist(
    playlist_id: str,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """F23 — Excluir playlist privada."""
    try:
        library_service.excluir_playlist(session, user, playlist_id)
    except library_service.PlaylistNotFound as exc:
        raise HTTPException(404, str(exc)) from exc
    return Response(status_code=204)


@router.put(
    "/api/library/playlists/{playlist_id}/lessons",
    response_model=PlaylistResponse,
)
def organizar_aulas_playlist(
    playlist_id: str,
    data: PlaylistLessonsUpdateRequest,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> PlaylistResponse:
    """F23 — Adicionar, remover e reordenar aulas da playlist."""
    try:
        return library_service.organizar_aulas_da_playlist(
            session, integrations, user, playlist_id, data.lesson_ids
        )
    except library_service.PlaylistNotFound as exc:
        raise HTTPException(404, str(exc)) from exc
    except library_service.PlaylistConflict as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get(
    "/api/library/playlists/{playlist_id}/playback/{lesson_id}",
    response_model=PlaylistPlaybackContextResponse,
)
def reproduzir_aula_na_playlist(
    playlist_id: str,
    lesson_id: str,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> PlaylistPlaybackContextResponse:
    """F23 — Reproduzir sequência dentro do contexto da playlist."""
    try:
        return library_service.obter_contexto_playlist(
            session, integrations, user, playlist_id, lesson_id
        )
    except (
        library_service.PlaylistNotFound,
        library_service.PlaylistLessonNotFound,
    ) as exc:
        raise HTTPException(404, str(exc)) from exc


# --- LessonInteractionController (F24, F25, F26) ---


@router.get(
    "/api/interactions/lessons/{lesson_id}/note",
    response_model=PrivateNoteResponse,
)
def consultar_anotacao(
    lesson_id: str,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> PrivateNoteResponse:
    """F24 — Recuperar anotação privada ao reabrir a aula."""
    return interaction_service.obter_anotacao_do_proprietario(
        session, integrations, user, lesson_id
    )


@router.put(
    "/api/interactions/lessons/{lesson_id}/note",
    response_model=PrivateNoteResponse,
)
def salvar_anotacao(
    lesson_id: str,
    data: PrivateNoteUpdateRequest,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> PrivateNoteResponse:
    """F24 — Criar ou editar anotação privada vinculada à aula."""
    return interaction_service.salvar_anotacao_privada(
        session, integrations, user, lesson_id, data.content
    )


@router.get(
    "/api/interactions/lessons/{lesson_id}/comments",
    response_model=list[CommentResponse],
)
def listar_comentarios(
    lesson_id: str,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> list[CommentResponse]:
    """F25 — Listar comentários públicos aprovados da aula."""
    return interaction_service.listar_comentarios_aula(
        session, integrations, user, lesson_id
    )


@router.post(
    "/api/interactions/lessons/{lesson_id}/comments",
    response_model=CommentResponse,
    status_code=201,
)
def publicar_comentario(
    lesson_id: str,
    data: CommentCreateRequest,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> CommentResponse:
    """F25 — Publicar comentário ou resposta na aula."""
    try:
        return interaction_service.publicar_comentario(
            session,
            integrations,
            user,
            lesson_id,
            data.content,
            data.parent_id,
        )
    except interaction_service.ParentCommentNotFound as exc:
        raise HTTPException(404, str(exc)) from exc


@router.put(
    "/api/interactions/ratings/{target_id}",
    response_model=RatingSummaryResponse,
)
def avaliar_conteudo(
    target_id: str,
    data: RatingUpdateRequest,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> RatingSummaryResponse:
    """F26 — Avaliar uma aula ou curso e recalcular média."""
    return interaction_service.registrar_avaliacao(
        session, integrations, user, data.target_type, target_id, data.stars
    )


@router.get(
    "/api/interactions/ratings/{target_id}",
    response_model=RatingSummaryResponse,
)
def consultar_avaliacao(
    target_id: str,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
    target_type: Annotated[Literal["lesson", "course"], Query()] = "lesson",
) -> RatingSummaryResponse:
    """F26 — Consultar avaliação e média de uma aula ou curso."""
    return interaction_service.consultar_avaliacao(
        session, integrations, user, target_type, target_id
    )
