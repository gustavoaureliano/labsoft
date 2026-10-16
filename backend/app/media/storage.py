import os
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

BACKEND_DIR = Path(__file__).resolve().parents[2]
STORAGE_ROOT = BACKEND_DIR / os.environ.get("STORAGE_DIR", "storage")
MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_BYTES", 100 * 1024 * 1024))
CHUNK_SIZE = 1024 * 1024

if MAX_UPLOAD_BYTES <= 0:
    raise ValueError("MAX_UPLOAD_BYTES deve ser positivo")


class UploadTooLarge(ValueError):
    pass


def save_video(source: BinaryIO, extension: str) -> tuple[str, int]:
    key = f"videos/{uuid4()}{extension}"
    path = STORAGE_ROOT / key
    path.parent.mkdir(parents=True, exist_ok=True)
    size = 0

    target = path.open("xb")
    try:
        with target:
            while chunk := source.read(CHUNK_SIZE):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise UploadTooLarge("O vídeo excede o tamanho máximo permitido")
                target.write(chunk)
            if size == 0:
                raise ValueError("O arquivo está vazio")
    except Exception:
        path.unlink(missing_ok=True)
        raise

    return key, size


def delete_video(key: str) -> None:
    (STORAGE_ROOT / key).unlink(missing_ok=True)
