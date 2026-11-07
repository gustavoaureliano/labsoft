from pathlib import Path
from typing import BinaryIO
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from PIL import Image, UnidentifiedImageError

from app.media import storage
from app.media.models import Media
from app.media.inspection import inspect_video

VIDEO_TYPES = {".mp4": "video/mp4", ".webm": "video/webm"}


class MediaNotFound(LookupError):
    pass


def get_media(session: Session, media_id: UUID, *, lock: bool = False) -> Media:
    query = select(Media).where(Media.id == media_id)
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    media = session.scalar(query)
    if media is None:
        raise MediaNotFound("Mídia não encontrada")
    return media


def upload_thumbnail(session: Session, source: BinaryIO, filename: str, content_type: str, owner_id: str) -> Media:
    filename = filename.replace("\\", "/").rsplit("/", 1)[-1]
    extension = Path(filename).suffix.lower()
    types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
    if not filename or len(filename) > 255 or types.get(extension) != content_type:
        raise ValueError("Envie uma imagem JPEG ou PNG")
    key, size = storage.save_file(source, extension, "thumbnails", 5 * 1024 * 1024)
    try:
        try:
            with Image.open(storage.get_video_path(key)) as image:
                if image.width * image.height > 20_000_000 or image.format not in {"JPEG", "PNG"}:
                    raise ValueError("Imagem inválida ou maior que 20 megapixels")
                expected = "PNG" if content_type == "image/png" else "JPEG"
                if image.format != expected:
                    raise ValueError("Conteúdo da imagem não corresponde ao tipo declarado")
                image.verify()
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
            raise ValueError("Imagem inválida") from exc
        media = Media(owner_id=owner_id, storage_key=key, original_filename=filename,
                      content_type=content_type, size_bytes=size, status="available")
        session.add(media)
        session.commit()
    except Exception:
        session.rollback()
        storage.delete_video(key)
        raise
    return media


def get_video_content(session: Session, media_id: UUID) -> tuple[Media, Path]:
    media = get_media(session, media_id)
    if media.status != "available":
        raise MediaNotFound("Vídeo indisponível")
    return media, storage.get_video_path(media.storage_key)


def upload_video(
    session: Session, source: BinaryIO, filename: str, content_type: str, owner_id: str
) -> Media:
    filename = filename.replace("\\", "/").rsplit("/", 1)[-1]
    if not filename or len(filename) > 255:
        raise ValueError("O nome do arquivo deve ter entre 1 e 255 caracteres")

    extension = Path(filename).suffix.lower()
    if extension not in VIDEO_TYPES or VIDEO_TYPES[extension] != content_type:
        raise ValueError("Envie um vídeo MP4 ou WebM com o tipo correspondente")

    key, size = storage.save_video(source, extension)
    try:
        info = inspect_video(storage.get_video_path(key), content_type)
        media = Media(
            duration_seconds=info.duration_seconds,
            codec=info.codec,
            owner_id=owner_id,
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
