from uuid import UUID, uuid4

import httpx
import pytest
from app import integrations
from app.courses.models import Course, CourseLesson


@pytest.fixture
def integrated(client, monkeypatch):
    uid = str(uuid4())
    state = {"role": "teacher", "lessons": [], "failure": False}
    monkeypatch.setenv("CATALOG_DEMO_MODE", "false")
    monkeypatch.setenv("IDENTITY_URL", "http://identity")
    monkeypatch.setenv("LEARNING_URL", "http://learning")
    monkeypatch.setenv("FRONTEND_ORIGIN", "http://testserver")
    original = httpx.Client
    def handle(req):
        assert req.headers["authorization"] == "Bearer real"
        assert "cookie" not in req.headers
        if req.url.path == "/api/v1/auth/me": return httpx.Response(200, json={"id": uid, "role": state["role"]})
        if req.url.path == "/api/v1/profiles/me": return httpx.Response(200, json={"user_id": uid, "display_name": "Nome real"})
        if state["failure"]: return httpx.Response(503)
        return httpx.Response(200, json={"course_id": req.url.path.split('/')[4], "items": state["lessons"]})
    monkeypatch.setattr(integrations.httpx, "Client", lambda **kw: original(transport=httpx.MockTransport(handle), **kw))
    client.headers["Authorization"] = "Bearer real"
    return client, uid, state


def create(client):
    response = client.post('/api/courses', json={"title": "Curso real", "subject": "Física", "summary": "Descrição do curso real", "access_type": "free"},
                           headers={"X-Teacher-Id": str(uuid4()), "X-Teacher-Name": "Forjado"})
    assert response.status_code == 201, response.text
    return response.json()


def test_owner_summary_and_duplicate_lesson_writes(integrated, db_session):
    client, uid, _ = integrated
    course = create(client)
    assert course['teacher_id'] == uid and course['teacher_name'] == 'Nome real'
    assert client.get(f"/api/courses/{course['id']}/summary").headers['cache-control'] == 'private, no-store'
    for _ in range(3): assert client.get(f"/api/courses/{course['id']}/summary").status_code == 200
    db_session.expire_all()
    assert db_session.get(Course, UUID(course['id'])).view_count == 0
    assert client.post(f"/api/courses/{course['id']}/lessons", json={"title": "Duplicada", "position": 0}).status_code == 410
    assert db_session.query(CourseLesson).count() == 0
    del client.headers['Authorization']
    assert client.get(f"/api/courses/{course['id']}/summary").status_code == 404


def test_publication_and_preview_use_remote_lessons(integrated, db_session):
    client, _, state = integrated
    course = create(client)
    url = f"/api/courses/{course['id']}/publication"
    assert client.post(url, json={"action": "publish"}).status_code == 422
    state['lessons'] = [{"id": str(uuid4()), "title": "Aula remota", "description": "Descrição remota", "position": 1, "duration_seconds": 12}]
    preview = client.get(f"/api/courses/{course['id']}/preview")
    assert preview.status_code == 200, preview.text
    assert preview.json()['lessons'][0]['title'] == 'Aula remota'
    assert client.post(url, json={"action": "publish"}).json()['status'] == 'published'
    assert db_session.query(CourseLesson).count() == 0


def test_remote_failure_does_not_publish(integrated, db_session):
    client, _, state = integrated
    course = create(client)
    state['failure'] = True
    assert client.post(f"/api/courses/{course['id']}/publication", json={"action": "publish"}).status_code == 503
    db_session.expire_all()
    assert db_session.get(Course, UUID(course['id'])).status == 'draft'


def test_real_student_cannot_create_course(integrated):
    client, _, state = integrated
    state['role'] = 'student'
    response = client.post('/api/courses',json={"title":"Inválido","subject":"Física","summary":"Descrição suficiente","access_type":"free"})
    assert response.status_code == 403
