from io import BytesIO
from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.media import service, storage
from app.media.models import Media


def assert_empty(sessions, root):
    with sessions() as session:
        assert session.scalar(select(func.count()).select_from(Media)) == 0
    assert not list(root.rglob("*.mp4"))
    assert not list(root.rglob("*.webm"))


@pytest.mark.parametrize("extension,content_type", [("mp4", "video/mp4"), ("webm", "video/webm")])
def test_upload_persists_file_and_metadata(upload_context, extension, content_type):
    client, sessions, root = upload_context
    content = b"video-demo" * 200_000
    response = client.post(
        "/api/media",
        files={"file": (f"../../aula.{extension}", content, content_type)},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["original_filename"] == f"aula.{extension}"
    assert data["size_bytes"] == len(content)
    assert data["status"] == "available"
    assert "storage_key" not in data
    with sessions() as session:
        media = session.get(Media, UUID(data["id"]))
        path = root / media.storage_key
        assert path.parent == root / "videos"
        UUID(path.stem)
        assert path.read_bytes() == content


@pytest.mark.parametrize("filename,content_type", [("aula.txt", "text/plain"), ("aula.mp4", "video/webm")])
def test_invalid_format_leaves_no_file_or_row(upload_context, filename, content_type):
    client, sessions, root = upload_context
    response = client.post("/api/media", files={"file": (filename, b"data", content_type)})
    assert response.status_code == 400
    assert_empty(sessions, root)


def test_oversized_upload_cleans_partial_file(upload_context, monkeypatch):
    client, sessions, root = upload_context
    monkeypatch.setattr(storage, "MAX_UPLOAD_BYTES", 8)
    monkeypatch.setattr(storage, "CHUNK_SIZE", 4)
    response = client.post("/api/media", files={"file": ("aula.mp4", b"123456789", "video/mp4")})
    assert response.status_code == 413
    assert_empty(sessions, root)


def test_empty_upload_is_rejected(upload_context):
    client, sessions, root = upload_context
    response = client.post("/api/media", files={"file": ("aula.mp4", b"", "video/mp4")})
    assert response.status_code == 400
    assert_empty(sessions, root)


def test_database_failure_removes_file_and_rolls_back(upload_context, monkeypatch):
    client, sessions, root = upload_context

    def failed_commit(session):
        session.flush()
        raise RuntimeError("Simulated commit failure")

    monkeypatch.setattr(Session, "commit", failed_commit)
    response = client.post("/api/media", files={"file": ("aula.mp4", b"data", "video/mp4")})
    assert response.status_code == 500
    assert_empty(sessions, root)


def test_invalid_service_response_is_server_error(upload_context, monkeypatch):
    client, _, _ = upload_context
    monkeypatch.setattr(service, "upload_video", lambda *args: object())

    response = client.post("/api/media", files={"file": ("aula.mp4", b"data", "video/mp4")})

    assert response.status_code == 500


def test_read_failure_removes_partial_file(upload_context, monkeypatch):
    _, sessions, root = upload_context
    monkeypatch.setattr(storage, "CHUNK_SIZE", 4)

    class BrokenSource(BytesIO):
        def read(self, size=-1):
            if self.tell() > 0:
                raise OSError("Simulated read failure")
            return super().read(size)

    with pytest.raises(OSError):
        storage.save_video(BrokenSource(b"12345678"), ".mp4")
    assert_empty(sessions, root)
