from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
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
