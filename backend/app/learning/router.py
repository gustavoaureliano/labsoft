from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_session
from app.integrations import Integrations, User, get_current_user, get_integrations
from app.permissions import require_course
from app.learning.models import Lesson
from app.media import service as media_service
from app.learning import service
from app.learning.schemas import (
    LessonCreate, LessonMediaUpdate, LessonPlaybackResponse, LessonResponse,
)
from app.media.service import MediaNotFound

router = APIRouter(prefix="/api/learning", tags=["Aprendizagem"])


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
    return LessonPlaybackResponse(
        **data,
        content_url=str(request.app.url_path_for(
            "get_media_content", media_id=str(lesson.media_id)
        )),
    )


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
        media = media_service.get_media(session, data.media_id)
        if media.owner_id != user.id:
            raise HTTPException(403, "A mídia não pertence ao professor")
        lesson = service.associate_media(session, lesson_id, data.media_id)
    except (service.LessonNotFound, MediaNotFound) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except service.MediaUnavailable as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return LessonResponse.model_validate(lesson)
