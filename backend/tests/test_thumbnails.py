from datetime import datetime, timedelta, timezone
from io import BytesIO
from uuid import UUID
from pathlib import Path

import pytest

from PIL import Image

from app.media.cleanup import cleanup
from app.media.models import Media
from tests.test_lessons import create_lesson, upload


def image_bytes():
    buffer = BytesIO()
    Image.new("RGB", (20, 20), "blue").save(buffer, "PNG")
    return buffer.getvalue()


def test_thumbnail_lifecycle(upload_context):
    client, _, _ = upload_context
    lesson = create_lesson(client)
    response = client.post("/api/media/thumbnails", files={"file": ("thumb.png", image_bytes(), "image/png")})
    assert response.status_code == 201
    media_id = response.json()["id"]
    url = f"/api/learning/lessons/{lesson['id']}"
    assert client.patch(url + "/thumbnail", json={"media_id": media_id}).json()["thumbnail_id"] == media_id
    assert client.patch(url + "/media", json={"media_id": media_id}).status_code == 409
    assert client.get(f"/api/media/{media_id}/content").headers["content-type"] == "image/png"
    assert client.patch(url + "/thumbnail", json={"media_id": None}).json()["thumbnail_id"] is None
    assert client.post("/api/media/thumbnails", files={"file": ("bad.png", b"bad", "image/png")}).status_code == 400


def test_cleanup_is_age_gated_and_preserves_references(upload_context):
    client, sessions, root = upload_context
    orphan, referenced, recent = upload(client), upload(client), upload(client)
    lesson = create_lesson(client)
    client.patch(f"/api/learning/lessons/{lesson['id']}/media", json={"media_id": referenced})
    with sessions() as session:
        for media_id in (orphan, referenced):
            session.get(Media, UUID(media_id)).created_at = datetime.now(timezone.utc) - timedelta(days=2)
        session.commit()
        assert cleanup(session, "professor-demo", 24) == [orphan]
        assert len(list(root.rglob("*.mp4"))) == 3
        assert cleanup(session, "professor-demo", 24, apply=True) == [orphan]
        assert session.get(Media, UUID(orphan)) is None
        assert session.get(Media, UUID(referenced)) is not None
        assert session.get(Media, UUID(recent)) is not None
        assert len(list(root.rglob("*.mp4"))) == 2


def test_cleanup_disk_failure_is_reported_and_record_remains(upload_context, monkeypatch):
    client, sessions, _ = upload_context
    media_id = upload(client)
    with sessions() as session:
        session.get(Media, UUID(media_id)).created_at = datetime.now(timezone.utc) - timedelta(days=2)
        session.commit()
        def fail(*args, **kwargs):
            raise OSError("Disk failure")
        with monkeypatch.context() as patch:
            patch.setattr(Path, "unlink", fail)
            with pytest.raises(OSError):
                cleanup(session, "professor-demo", 24, apply=True)
        session.rollback()
        assert session.get(Media, UUID(media_id)) is not None


def test_thumbnail_size_limit_and_other_owner_cleanup(upload_context):
    client, sessions, root = upload_context
    response = client.post("/api/media/thumbnails", files={"file": ("big.png", b"x" * (5 * 1024 * 1024 + 1), "image/png")})
    assert response.status_code == 413
    assert not list(root.rglob("*.png"))
    media_id = upload(client)
    with sessions() as session:
        session.get(Media, UUID(media_id)).created_at = datetime.now(timezone.utc) - timedelta(days=2)
        session.commit()
        assert cleanup(session, "professor-demo-2", 24, apply=True) == []
        assert session.get(Media, UUID(media_id)) is not None
