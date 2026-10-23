"""Local media storage and short-lived download signatures."""

import hashlib
import hmac
import os
import re
import time
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile


MAX_UPLOAD_BYTES = 50 * 1024 * 1024


class LocalMediaStorage:
    def __init__(self) -> None:
        self.root = Path(os.environ.get("MEDIA_ROOT", "var/media")).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.signing_key = os.environ.get(
            "MEDIA_SIGNING_KEY", "development-only-change-me"
        ).encode()

    def save(self, upload: UploadFile) -> tuple[str, int]:
        safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", upload.filename or "file")
        storage_key = f"{uuid4()}/{safe_name}"
        destination = (self.root / storage_key).resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        size = 0
        try:
            with destination.open("wb") as output:
                while chunk := upload.file.read(1024 * 1024):
                    size += len(chunk)
                    if size > MAX_UPLOAD_BYTES:
                        raise ValueError("Arquivo excede o limite de 50 MB.")
                    output.write(chunk)
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        return storage_key, size

    def delete(self, storage_key: str) -> None:
        path = self.path(storage_key)
        path.unlink(missing_ok=True)
        try:
            path.parent.rmdir()
        except OSError:
            pass

    def path(self, storage_key: str) -> Path:
        path = (self.root / storage_key).resolve()
        if self.root not in path.parents:
            raise ValueError("Chave de armazenamento inválida.")
        return path

    def signed_url(self, media_id: UUID, lifetime_seconds: int = 300) -> str:
        expires = int(time.time()) + lifetime_seconds
        message = f"{media_id}:{expires}".encode()
        signature = hmac.new(self.signing_key, message, hashlib.sha256).hexdigest()
        return f"/api/media/{media_id}/download?expires={expires}&signature={signature}"

    def validate(self, media_id: UUID, expires: int, signature: str) -> bool:
        if expires < int(time.time()):
            return False
        message = f"{media_id}:{expires}".encode()
        expected = hmac.new(self.signing_key, message, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
