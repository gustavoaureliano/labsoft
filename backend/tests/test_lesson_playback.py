from uuid import UUID

import pytest

from app.media.models import Media


@pytest.fixture
def playback_context(upload_context):
    client, sessions, root = upload_context
    response = client.post("/api/learning/lessons", json={
        "course_id": "fisica-quantica", "title": "Introdução",
        "description": "Conceitos iniciais", "position": 1,
    })
    assert response.status_code == 201
    lesson = response.json()
    return client, sessions, root, lesson


def attach_video(client, lesson):
    content = b"video-playback-test"
    response = client.post("/api/media", files={"file": ("aula.mp4", content, "video/mp4")})
    assert response.status_code == 201
    media = response.json()
    response = client.patch(
        f"/api/learning/lessons/{lesson['id']}/media", json={"media_id": media["id"]}
    )
    assert response.status_code == 200
    return media, content


def test_playback_returns_lesson_and_working_content_url(playback_context):
    client, _, _, lesson = playback_context
    media, content = attach_video(client, lesson)
    response = client.get(f"/api/learning/lessons/{lesson['id']}/playback")
    assert response.status_code == 200
    assert response.json() == {
        **lesson, "media_id": media["id"],
        "content_url": f"/api/media/{media['id']}/content",
        "duration_seconds": 12.0, "position_seconds": 0, "completed": False,
    }
    video = client.get(response.json()["content_url"], headers={"Range": "bytes=0-3"})
    assert video.status_code == 206
    assert video.content == content[:4]


def test_unknown_lesson(upload_context):
    client, _, _ = upload_context
    assert client.get("/api/learning/lessons/missing/playback").status_code == 404


def test_lesson_without_video(playback_context):
    client, _, _, lesson = playback_context
    assert client.get(f"/api/learning/lessons/{lesson['id']}/playback").status_code == 409


@pytest.mark.parametrize("state", ["pending", "failed"])
def test_unavailable_media(playback_context, state):
    client, sessions, _, lesson = playback_context
    media, _ = attach_video(client, lesson)
    with sessions() as session:
        session.get(Media, UUID(media["id"])).status = state
        session.commit()
    assert client.get(f"/api/learning/lessons/{lesson['id']}/playback").status_code == 404


def test_missing_file(playback_context):
    client, sessions, root, lesson = playback_context
    media, _ = attach_video(client, lesson)
    with sessions() as session:
        record = session.get(Media, UUID(media["id"]))
        (root / record.storage_key).unlink()
    assert client.get(f"/api/learning/lessons/{lesson['id']}/playback").status_code == 404
