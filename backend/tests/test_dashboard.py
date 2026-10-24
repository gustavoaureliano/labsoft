from app.integrations import DemoIntegrations, get_current_user, get_integrations
from app.main import app
from tests.test_lessons import create_lesson, upload


def test_courses_progress_and_continuation(upload_context):
    client, _, _ = upload_context
    first, second = create_lesson(client), create_lesson(client, 2)
    media_id = upload(client)
    for lesson in (first, second):
        client.patch(f"/api/learning/lessons/{lesson['id']}/media", json={"media_id": media_id})
    app.dependency_overrides[get_current_user] = lambda: DemoIntegrations.users["aluno-demo"]
    course_url = "/api/learning/courses/fisica-quantica"
    data = client.get(course_url).json()
    assert data["progress"] == 0 and data["continue_lesson"]["id"] == first["id"]
    client.patch(f"/api/learning/lessons/{first['id']}/progress", json={"media_id": media_id, "position_seconds": 11})
    data = client.get(course_url).json()
    assert data["progress"] == 50 and data["continue_lesson"]["id"] == second["id"]
    assert client.get("/api/learning/dashboard").json()["current_course"]["id"] == "fisica-quantica"
    assert not client.get("/api/learning/courses/fisica-enem-mecanica").json()["completed"]
    app.dependency_overrides[get_current_user] = lambda: DemoIntegrations.users["aluno-demo-2"]
    assert client.get(course_url).status_code == 403
    assert len(client.get("/api/learning/courses").json()) == 1


def test_optional_service_failure_does_not_hide_panel(upload_context):
    client, _, _ = upload_context
    class Unavailable(DemoIntegrations):
        def recommendations(self, student_id):
            raise RuntimeError("unavailable")
        def notifications(self, user_id):
            raise RuntimeError("unavailable")
    app.dependency_overrides[get_integrations] = Unavailable
    app.dependency_overrides[get_current_user] = lambda: DemoIntegrations.users["aluno-demo"]
    response = client.get("/api/learning/dashboard")
    assert response.status_code == 200
    assert response.json()["current_course"] is None
    assert response.json()["recommendations"] == []


def test_expired_and_blocked_courses_have_no_playback_details(upload_context):
    client, _, _ = upload_context
    app.dependency_overrides[get_current_user] = lambda: DemoIntegrations.users["aluno-acesso-demo"]
    courses = {course["id"]: course for course in client.get("/api/learning/courses").json()}
    assert {key: course["access_status"] for key, course in courses.items()} == {
        "fisica-quantica": "expired", "fisica-enem-mecanica": "active", "biologia-celular": "blocked",
    }
    for key in ("fisica-quantica", "biologia-celular"):
        assert courses[key]["lessons"] == []
        assert courses[key]["continue_lesson"] is None
        assert client.get(f"/api/learning/courses/{key}").status_code == 403
    assert client.get("/api/learning/dashboard").json()["courses"][0]["id"] == "fisica-enem-mecanica"
    assert len(client.get("/api/learning/dashboard").json()["courses"]) == 1
