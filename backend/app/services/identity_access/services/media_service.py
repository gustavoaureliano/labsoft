from __future__ import annotations

import hashlib

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import MediaItem, User
from .errors import ServiceError
from .identity_service import IdentityService


class MediaService:

    _EXT = {
        "application/pdf": ".pdf",
        "image/jpeg": ".jpg",
        "image/png": ".png",
    }

    def __init__(
        self,
        settings: Settings,
    ):
        self.settings = settings

    @classmethod
    def _identify(
        cls,
        beginning: bytes,
    ) -> str | None:

        if beginning.startswith(b"%PDF-"):
            return "application/pdf"

        if beginning.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"

        if beginning.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"

        return None

    def upload_document(
        self,
        db: Session,
        user: User,
        upload: UploadFile,
    ) -> MediaItem:

        original_name = (
            (upload.filename or "")
            .replace("\\", "/")
            .split("/")[-1]
        )

        if (
            not original_name
            or len(original_name) > 255
        ):
            raise ServiceError(
                "invalid",
                "Nome de arquivo inválido.",
            )

        ext = Path(
            original_name
        ).suffix.lower()

        root = self.settings.media_root.resolve()

        root.mkdir(
            parents=True,
            exist_ok=True,
            mode=0o700,
        )

        storage_name = uuid4().hex
        file_path = root / storage_name

        total = 0
        sha = hashlib.sha256()
        first = b""

        try:
            with file_path.open("xb") as output:

                file_path.chmod(0o600)

                while chunk := upload.file.read(
                    64 * 1024
                ):

                    if not first:
                        first = chunk[:16]

                    total += len(chunk)

                    if (
                        total
                        > self.settings.max_document_bytes
                    ):
                        raise ServiceError(
                            "too_large",
                            "Documento excede "
                            "o limite permitido.",
                        )

                    sha.update(chunk)
                    output.write(chunk)

            mime = self._identify(first)

            if (
                mime is None
                or ext not in (
                    {".jpg", ".jpeg"}
                    if mime == "image/jpeg"
                    else {self._EXT.get(mime)}
                )
            ):
                raise ServiceError(
                    "invalid",
                    "Documento inválido; envie PDF, "
                    "JPEG ou PNG compatível.",
                )

            if total == 0:
                raise ServiceError(
                    "invalid",
                    "Documento vazio.",
                )

            media = MediaItem(
                user_id=user.id,
                original_name=original_name,
                storage_name=storage_name,
                content_type=mime,
                size_bytes=total,
                checksum_sha256=sha.hexdigest(),
            )

            db.add(media)
            db.flush()

            return media

        except Exception:
            file_path.unlink(
                missing_ok=True
            )
            raise

    def find_authorized(
        self,
        db: Session,
        user: User,
        media_id: str,
    ) -> tuple[MediaItem, Path]:

        media = db.get(
            MediaItem, media_id
        )

        if media is None:
            raise ServiceError(
                "not_found",
                "Documento não encontrado.",
            )

        IdentityService.require_owner(
            user,
            media.user_id,
            allow_admin=True,
        )

        path = (
            self.settings.media_root.resolve()
            / media.storage_name
        )

        if not path.is_file():
            raise ServiceError(
                "not_found",
                "Arquivo não está disponível.",
            )

        return media, path