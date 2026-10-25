from app.integrations import DemoIntegrations, get_current_user
from app.main import app
from tests.test_lessons import create_lesson, upload
import pytest


@pytest.mark.parametrize("position", ["NaN", "Infinity", "-Infinity"])
def test_nonfinite_progress_is_rejected(upload_context, position):
    client, _, _ = upload_context
    response = client.patch("/api/learning/lessons/any/progress", json={"media_id": "00000000-0000-0000-0000-000000000000", "position_seconds": position})
    assert response.status_code == 422


def test_resume_completion_rewind_and_media_replacement(upload_context):
    client, _, _ = upload_context
    lesson = create_lesson(client, course_id="fisica-enem-mecanica")
    media_id = upload(client)
    base = f"/api/learning/lessons/{lesson['id']}"
    client.patch(base + "/media", json={"media_id": media_id})
    app.dependency_overrides[get_current_user] = lambda: DemoIntegrations.users["aluno-demo"]
    for position in [4, 11, 2]:
        response = client.patch(base + "/progress", json={"media_id": media_id, "position_seconds": position})
        assert response.status_code == 200
    assert response.json()["completed"] is True
    assert client.get(base + "/playback").json()["position_seconds"] == 2
    app.dependency_overrides[get_current_user] = lambda: DemoIntegrations.users["aluno-demo-2"]
    assert client.get(base + "/playback").json()["position_seconds"] == 0
    assert client.patch(base + "/progress", json={"media_id": media_id, "position_seconds": -1}).status_code == 422
    assert client.patch(base + "/progress", json={"media_id": media_id, "position_seconds": 13}).status_code == 400
    assert client.patch(base + "/progress", json={"media_id": media_id, "position_seconds": 1, "student_id": "other"}).status_code == 422
    app.dependency_overrides[get_current_user] = lambda: DemoIntegrations.users["professor-demo"]
    new_media = upload(client)
    client.patch(base + "/media", json={"media_id": new_media})
    assert client.patch(base + "/progress", json={"media_id": new_media, "position_seconds": 1}).status_code == 403
    app.dependency_overrides[get_current_user] = lambda: DemoIntegrations.users["aluno-demo"]
    data = client.get(base + "/playback").json()
    assert data["position_seconds"] == 0 and not data["completed"]
    assert client.patch(base + "/progress", json={"media_id": media_id, "position_seconds": 1}).status_code == 409


def test_completion_threshold_and_course_progress(upload_context):
    client, _, _ = upload_context
    lesson = create_lesson(client)
    media_id = upload(client)
    base = f"/api/learning/lessons/{lesson['id']}"
    assert client.patch(base + "/media", json={"media_id": media_id}).status_code == 200
    app.dependency_overrides[get_current_user] = lambda: DemoIntegrations.users["aluno-demo"]

    def save(position):
        return client.patch(base + "/progress", json={"media_id": media_id, "position_seconds": position})

    assert save(10.79).json()["completed"] is False
    assert client.get("/api/learning/courses/fisica-quantica").json()["progress"] == 0
    assert save(10.8).json()["completed"] is True  # 90% de 12 segundos
    assert client.get("/api/learning/courses/fisica-quantica").json()["completed"] is True
    assert save(12.01).status_code == 400
    assert save(1).json()["completed"] is True
    assert client.get(base + "/playback").json()["position_seconds"] == 1
