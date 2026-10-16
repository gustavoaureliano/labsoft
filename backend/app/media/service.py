from pathlib import Path
from typing import BinaryIO

from sqlalchemy.orm import Session

from app.media import storage
from app.media.models import Media

VIDEO_TYPES = {".mp4": "video/mp4", ".webm": "video/webm"}


def upload_video(
    session: Session, source: BinaryIO, filename: str, content_type: str
) -> Media:
    filename = filename.replace("\\", "/").rsplit("/", 1)[-1]
    if not filename or len(filename) > 255:
        raise ValueError("O nome do arquivo deve ter entre 1 e 255 caracteres")

    extension = Path(filename).suffix.lower()
    if extension not in VIDEO_TYPES or VIDEO_TYPES[extension] != content_type:
        raise ValueError("Envie um vídeo MP4 ou WebM com o tipo correspondente")

    key, size = storage.save_video(source, extension)
    try:
        media = Media(
            storage_key=key,
            original_filename=filename,
            content_type=content_type,
            size_bytes=size,
            status="available",
        )
        session.add(media)
        session.commit()
    except Exception:
        try:
            session.rollback()
        finally:
            storage.delete_video(key)
        raise

    return media
