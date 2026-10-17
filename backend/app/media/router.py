from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_session
from app.media import service
from app.media.schemas import MediaResponse
from app.media.storage import UploadTooLarge

router = APIRouter(prefix="/api/media", tags=["Mídia"])


@router.post("", response_model=MediaResponse, status_code=status.HTTP_201_CREATED)
def upload_media(
    file: UploadFile, session: Annotated[Session, Depends(get_session)]
) -> MediaResponse:
    try:
        media = service.upload_video(
            session, file.file, file.filename or "", file.content_type or ""
        )
    except UploadTooLarge as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        file.file.close()

    return MediaResponse.model_validate(media)


@router.get("/{media_id}", response_model=MediaResponse)
def get_media(
    media_id: UUID, session: Annotated[Session, Depends(get_session)]
) -> MediaResponse:
    try:
        media = service.get_media(session, media_id)
    except service.MediaNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return MediaResponse.model_validate(media)


@router.get(
    "/{media_id}/content",
    response_class=FileResponse,
    responses={
        200: {"content": {"video/mp4": {}, "video/webm": {}}},
        206: {"description": "Trecho do vídeo solicitado por HTTP Range"},
        404: {"description": "Mídia indisponível ou arquivo não encontrado"},
        416: {"description": "Intervalo solicitado fora do arquivo"},
    },
)
def get_media_content(
    media_id: UUID, session: Annotated[Session, Depends(get_session)]
) -> FileResponse:
    try:
        media, path = service.get_video_content(session, media_id)
    except (service.MediaNotFound, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileResponse(
        path,
        media_type=media.content_type,
        filename=media.original_filename,
        content_disposition_type="inline",
    )
