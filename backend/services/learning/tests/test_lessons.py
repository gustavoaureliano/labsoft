from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.learning.models import Lesson
from app.media.models import Media


def create_lesson(client, position=1, course_id="fisica-quantica"):
    response = client.post("/api/learning/lessons", json={
        "course_id": course_id, "title": "Introdução", "position": position,
    })
    assert response.status_code == 201
    return response.json()


def upload(client):
    response = client.post("/api/media", files={"file": ("aula.mp4", b"video", "video/mp4")})
    assert response.status_code == 201
    return response.json()["id"]


def test_create_upload_associate_and_list(upload_context):
    client, _, _ = upload_context
    lesson = create_lesson(client)
    assert lesson["media_id"] is None
    assert lesson["description"] == ""
    UUID(lesson["id"])
    media_id = upload(client)
    response = client.patch(f"/api/learning/lessons/{lesson['id']}/media", json={"media_id": media_id})
    assert response.status_code == 200
    assert response.json()["media_id"] == media_id
    lessons = client.get("/api/learning/courses/fisica-quantica/lessons").json()
    assert lessons == [response.json()]


def test_lessons_are_ordered_and_filtered(upload_context):
    client, _, _ = upload_context
    second = create_lesson(client, 2)
    first = create_lesson(client, 1)
    create_lesson(client, 1, "fisica-enem-mecanica")
    response = client.get("/api/learning/courses/fisica-quantica/lessons")
    assert [item["id"] for item in response.json()] == [first["id"], second["id"]]
    assert client.get("/api/learning/courses/sem-aulas/lessons").status_code == 404


def test_duplicate_position(upload_context):
    client, _, _ = upload_context
    create_lesson(client)
    response = client.post("/api/learning/lessons", json={
        "course_id": "fisica-quantica", "title": "Duplicada", "position": 1,
    })
    assert response.status_code == 409


@pytest.mark.parametrize("changes", [{"position": 0}, {"title": "   "}, {"course_id": ""}])
def test_invalid_lesson(upload_context, changes):
    client, _, _ = upload_context
    data = {"course_id": "fisica-quantica", "title": "Introdução", "position": 1}
    data.update(changes)
    assert client.post("/api/learning/lessons", json=data).status_code == 422


def test_missing_lesson_or_media(upload_context):
    client, _, _ = upload_context
    media_id = upload(client)
    assert client.patch("/api/learning/lessons/missing/media", json={"media_id": media_id}).status_code == 404
    lesson = create_lesson(client)
    assert client.patch(f"/api/learning/lessons/{lesson['id']}/media", json={"media_id": str(uuid4())}).status_code == 404


@pytest.mark.parametrize("state", ["pending", "failed"])
def test_unavailable_media_is_not_associated(upload_context, state):
    client, sessions, _ = upload_context
    lesson = create_lesson(client)
    media_id = upload(client)
    with sessions() as session:
        session.get(Media, UUID(media_id)).status = state
        session.commit()
    response = client.patch(f"/api/learning/lessons/{lesson['id']}/media", json={"media_id": media_id})
    assert response.status_code == 409
    with sessions() as session:
        assert session.get(Lesson, lesson["id"]).media_id is None


def test_replacement_preserves_old_media(upload_context):
    client, sessions, root = upload_context
    lesson = create_lesson(client)
    first, second = upload(client), upload(client)
    url = f"/api/learning/lessons/{lesson['id']}/media"
    for media_id in (first, second, second):
        response = client.patch(url, json={"media_id": media_id})
        assert response.status_code == 200
    with sessions() as session:
        assert str(session.get(Lesson, lesson["id"]).media_id) == second
        assert len(list(session.scalars(select(Media)))) == 2
        assert (root / session.get(Media, UUID(first)).storage_key).is_file()
