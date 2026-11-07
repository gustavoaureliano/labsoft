from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.database import get_session
from app.integrations import Integrations, User, get_current_user, get_integrations
from app.permissions import require_course
from app.learning.models import Lesson
from app.media import service as media_service
from app.learning import progress
from app.learning import dashboard
from app.learning.schemas import ProgressResponse, ProgressUpdate
from app.learning import service
from app.learning.schemas import (
    LessonCreate, LessonMediaUpdate, LessonPlaybackResponse, LessonResponse, LessonUpdate, LessonOrder,
)
from app.media.service import MediaNotFound

router = APIRouter(prefix="/api/learning", tags=["Aprendizagem"])


@router.get("/courses")
def learning_courses(
    session: Annotated[Session, Depends(get_session)], user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> list[dict]:
    return dashboard.learning_courses(session, user, integrations)


@router.get("/courses/{course_id}")
def course_detail(
    course_id: str, session: Annotated[Session, Depends(get_session)], user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> dict:
    course = require_course(user, integrations, course_id)
    return dashboard.course_detail(session, user, course)


@router.get("/dashboard")
def learning_dashboard(
    session: Annotated[Session, Depends(get_session)], user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> dict:
    if user.role != "student":
        raise HTTPException(403, "Painel exclusivo do aluno")
    return dashboard.dashboard(session, user, integrations)


@router.patch("/lessons/{lesson_id}/thumbnail", response_model=LessonResponse)
def associate_thumbnail(
    lesson_id: str, data: LessonMediaUpdate, session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> LessonResponse:
    try:
        lesson = service.get_lesson(session, lesson_id)
        require_course(user, integrations, lesson.course_id, write=True)
        if data.media_id is not None:
            media = media_service.get_media(session, data.media_id)
            if media.owner_id != user.id:
                raise HTTPException(403, "Imagem não pertence ao professor")
        lesson = service.associate_thumbnail(session, lesson, data.media_id)
    except (service.LessonNotFound, MediaNotFound) as exc:
        raise HTTPException(404, str(exc)) from exc
    except service.MediaUnavailable as exc:
        raise HTTPException(409, str(exc)) from exc
    return LessonResponse.model_validate(lesson)


@router.get("/lessons/{lesson_id}/playback", response_model=LessonPlaybackResponse)
def get_playback(
    lesson_id: str, request: Request,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> LessonPlaybackResponse:
    try:
        lesson_record = session.get(Lesson, lesson_id)
        if lesson_record is None:
            raise service.LessonNotFound("Aula não encontrada")
        require_course(user, integrations, lesson_record.course_id)
        lesson = service.get_playback(session, lesson_id)
    except (service.LessonNotFound, MediaNotFound, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except service.MediaUnavailable as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    data = LessonResponse.model_validate(lesson).model_dump()
    media = media_service.get_media(session, lesson.media_id)
    saved = progress.get_progress(session, user.id, lesson) if user.role == "student" else ProgressResponse(position_seconds=0, completed=False)
    return LessonPlaybackResponse(
        **data,
        duration_seconds=media.duration_seconds,
        position_seconds=saved.position_seconds,
        completed=saved.completed,
        content_url=str(request.app.url_path_for(
            "get_media_content", media_id=str(lesson.media_id)
        )),
    )


@router.patch("/lessons/{lesson_id}/progress", response_model=ProgressResponse)
def save_progress(
    lesson_id: str, data: ProgressUpdate, session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> ProgressResponse:
    if user.role != "student":
        raise HTTPException(403, "Prévia do professor não registra progresso")
    try:
        lesson = service.get_lesson(session, lesson_id)
        require_course(user, integrations, lesson.course_id)
        return progress.save_progress(session, user.id, lesson_id, data.media_id, data.position_seconds)
    except (service.LessonNotFound, MediaNotFound) as exc:
        raise HTTPException(404, str(exc)) from exc
    except service.MediaUnavailable as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/lessons", response_model=LessonResponse, status_code=201)
def create_lesson(
    data: LessonCreate, session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> LessonResponse:
    require_course(user, integrations, data.course_id, write=True)
    try:
        lesson = service.create_lesson(session, data)
    except service.LessonPositionConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return LessonResponse.model_validate(lesson)


@router.get("/courses/{course_id}/lessons", response_model=list[LessonResponse])
def list_lessons(
    course_id: str, session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> list[LessonResponse]:
    require_course(user, integrations, course_id)
    return [LessonResponse.model_validate(lesson) for lesson in service.list_lessons(session, course_id)]


@router.patch("/lessons/{lesson_id}/media", response_model=LessonResponse)
def associate_media(
    lesson_id: str, data: LessonMediaUpdate,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> LessonResponse:
    try:
        existing = session.get(Lesson, lesson_id)
        if existing is None:
            raise service.LessonNotFound("Aula não encontrada")
        require_course(user, integrations, existing.course_id, write=True)
        if data.media_id is not None:
            media = media_service.get_media(session, data.media_id)
            if media.owner_id != user.id:
                raise HTTPException(403, "A mídia não pertence ao professor")
        lesson = service.associate_media(session, lesson_id, data.media_id)
    except (service.LessonNotFound, MediaNotFound) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except service.MediaUnavailable as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return LessonResponse.model_validate(lesson)


@router.patch("/lessons/{lesson_id}", response_model=LessonResponse)
def update_lesson(
    lesson_id: str, data: LessonUpdate, session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> LessonResponse:
    try:
        lesson = service.get_lesson(session, lesson_id)
        require_course(user, integrations, lesson.course_id, write=True)
        lesson = service.update_lesson(session, lesson, data)
    except service.LessonNotFound as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return LessonResponse.model_validate(lesson)


@router.delete("/lessons/{lesson_id}", status_code=204)
def delete_lesson(
    lesson_id: str, session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> Response:
    try:
        lesson = service.get_lesson(session, lesson_id)
    except service.LessonNotFound as exc:
        raise HTTPException(404, str(exc)) from exc
    require_course(user, integrations, lesson.course_id, write=True)
    service.delete_lesson(session, lesson)
    return Response(status_code=204)


@router.put("/courses/{course_id}/lessons/order", response_model=list[LessonResponse])
def reorder_lessons(
    course_id: str, data: LessonOrder, session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    integrations: Annotated[Integrations, Depends(get_integrations)],
) -> list[LessonResponse]:
    require_course(user, integrations, course_id, write=True)
    try:
        lessons = service.reorder_lessons(session, course_id, data.lesson_ids)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return [LessonResponse.model_validate(lesson) for lesson in lessons]
