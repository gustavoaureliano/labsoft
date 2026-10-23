"""QuestionController and NotificationController HTTP routes (F29-F32)."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.communication import notifications as notification_service
from app.communication import questions as question_service
from app.communication.schemas import (
    NotificationReadResponse,
    NotificationResponse,
    QuestionAnswerRequest,
    QuestionCreateRequest,
    QuestionResponse,
)
from app.database import get_session
from app.integrations import Integrations, User, get_current_user, get_integrations

router = APIRouter(tags=["Comunicação"])


@router.post("/api/questions", response_model=QuestionResponse, status_code=201)
def enviar_duvida(
    data: QuestionCreateRequest,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> QuestionResponse:
    """F29 — Enviar dúvida privada sobre o curso ou aula."""
    try:
        return question_service.criar_duvida_privada(
            session, integrations, user, data.course_id, data.lesson_id, data.prompt
        )
    except question_service.QuestionNotFound as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get("/api/questions/me", response_model=list[QuestionResponse])
def listar_minhas_duvidas(
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> list[QuestionResponse]:
    """F30 — Acompanhar dúvidas enviadas pelo aluno."""
    return question_service.consultar_duvidas_do_aluno(session, integrations, user)


@router.get("/api/questions/teacher", response_model=list[QuestionResponse])
def listar_duvidas_professor(
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
    status: Annotated[Literal["all", "pending", "answered"], Query()] = "all",
) -> list[QuestionResponse]:
    """F31 — Listar dúvidas destinadas ao professor."""
    return question_service.buscar_duvidas_destinadas(
        session, integrations, user, status
    )


@router.patch(
    "/api/questions/{question_id}/answer", response_model=QuestionResponse
)
def responder_duvida(
    question_id: str,
    data: QuestionAnswerRequest,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> QuestionResponse:
    """F31 — Responder dúvida e notificar o aluno."""
    try:
        return question_service.registrar_resposta(
            session, integrations, user, question_id, data.answer
        )
    except question_service.QuestionNotFound as exc:
        raise HTTPException(404, str(exc)) from exc
    except question_service.QuestionAccessDenied as exc:
        raise HTTPException(403, str(exc)) from exc


@router.get("/api/notifications", response_model=list[NotificationResponse])
def listar_notificacoes(
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[NotificationResponse]:
    """F32 — Consultar notificações do usuário autenticado."""
    records = notification_service.obter_avisos_do_usuario(session, user.id)
    return [NotificationResponse.model_validate(item) for item in records]


@router.patch(
    "/api/notifications/{notification_id}/read",
    response_model=NotificationReadResponse,
)
def marcar_como_lido(
    notification_id: str,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> NotificationReadResponse:
    """F32 — Marcar aviso como lido e retornar link de redirecionamento."""
    try:
        record = notification_service.confirmar_leitura(
            session, user.id, notification_id
        )
    except notification_service.NotificationNotFound as exc:
        raise HTTPException(404, str(exc)) from exc
    return NotificationReadResponse(
        id=record.id,
        is_read=record.is_read,
        destination_url=record.destination_url,
    )
