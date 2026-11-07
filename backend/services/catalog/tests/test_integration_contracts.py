from uuid import UUID, uuid4

import httpx
import pytest
from app import integrations
from app.courses.models import Course, CourseLesson, CourseMaterial


@pytest.fixture
def integrated(client, monkeypatch):
    uid = str(uuid4())
    state = {"role": "teacher", "lessons": [], "failure": False, "access": True}
    monkeypatch.setenv("CATALOG_DEMO_MODE", "false")
    monkeypatch.setenv("IDENTITY_URL", "http://identity")
    monkeypatch.setenv("LEARNING_URL", "http://learning")
    monkeypatch.setenv("ACCESS_URL", "http://access")
    monkeypatch.setenv("FRONTEND_ORIGIN", "http://testserver")
    original = httpx.Client
    def handle(req):
        assert req.headers["authorization"] == "Bearer real"
        assert "cookie" not in req.headers
        if req.url.path == "/api/v1/auth/me": return httpx.Response(200, json={"id": uid, "role": state["role"]})
        if req.url.path == "/api/v1/profiles/me": return httpx.Response(200, json={"user_id": uid, "display_name": "Nome real"})
        if state["failure"]: return httpx.Response(503)
        if req.url.host == "access": return httpx.Response(200, json={"user_id": uid, "course_id": req.url.params["course_id"], "allowed": state["access"]})
        requested = req.url.path.split('/')[4]
        items = state["lessons"] if requested == state.get("lesson_course", requested) else []
        return httpx.Response(200, json={"course_id": requested, "items": items})
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


def test_remote_lesson_reference_rejects_wrong_course_and_dependency_failure(integrated, db_session):
    client, _, state = integrated
    course = create(client)
    target = f"/api/courses/{course['id']}/materials"
    lesson_id = uuid4()
    material = {"title":"Lista de revisão", "kind":"PDF", "external_url":"https://example.com/lista.pdf",
                "lesson_id":str(lesson_id), "access_level":"enrolled"}
    assert client.post(target, json=material).status_code == 404
    state['lessons'] = [{"id":str(lesson_id), "title":"Aula real", "position":1, "duration_seconds":12}]
    state['lesson_course'] = course['id']
    state['failure'] = True
    assert client.post(target, json=material).status_code == 503
    state['failure'] = False
    response = client.post(target, json=material)
    assert response.status_code == 201, response.text
    assert db_session.query(CourseMaterial).count() == 1
    assert db_session.query(CourseLesson).count() == 0
    assert db_session.query(CourseMaterial).one().lesson_id == lesson_id
    other_course = create(client)
    assert client.post(f"/api/courses/{other_course['id']}/materials", json=material).status_code == 404
    assert client.patch(f"{target}/{response.json()['id']}", json={"lesson_id":str(uuid4())}).status_code == 404
    assert db_session.query(CourseMaterial).one().lesson_id == lesson_id


def test_signed_download_rechecks_current_access(integrated):
    client, _, state = integrated
    course = create(client)
    lesson_id = uuid4()
    state['lessons'] = [{"id":str(lesson_id), "title":"Aula real", "position":1, "duration_seconds":12}]
    response = client.post(f"/api/courses/{course['id']}/materials/upload",
                           data={"title":"Apostila protegida", "kind":"PDF", "access_level":"enrolled", "lesson_id":str(lesson_id)},
                           files={"file":("apostila.pdf", b"%PDF-1.4\nconteudo privado", "application/pdf")})
    assert response.status_code == 201, response.text
    client.post(f"/api/courses/{course['id']}/publication", json={"action":"publish"}).raise_for_status()
    state['role'] = 'student'
    listing = client.get(f"/api/courses/{course['id']}/materials?lesson_id={lesson_id}")
    assert listing.status_code == 200, listing.text
    signed_url = listing.json()['items'][0]['download_url']
    assert signed_url and signed_url.startswith('/api/media/')
    downloaded = client.get(signed_url)
    assert downloaded.status_code == 200 and downloaded.content.startswith(b'%PDF')
    assert downloaded.headers['cache-control'] == 'private, no-store'
    state['access'] = False
    assert client.get(signed_url).status_code == 403
    blocked = client.get(f"/api/courses/{course['id']}/materials?lesson_id={lesson_id}")
    assert blocked.json()['items'][0]['download_url'] is None
    assert blocked.json()['items'][0]['external_url'] is None


def test_signed_url_does_not_bypass_unpublication(integrated):
    client, _, state = integrated
    course = create(client)
    state['lessons'] = [{"id":str(uuid4()), "title":"Aula real", "position":1, "duration_seconds":12}]
    response = client.post(f"/api/courses/{course['id']}/materials/upload",
                           data={"title":"Lista pública", "kind":"PDF", "access_level":"public"},
                           files={"file":("lista.pdf", b"%PDF-1.4\nconteudo", "application/pdf")})
    assert response.status_code == 201
    client.post(f"/api/courses/{course['id']}/publication", json={"action":"publish"}).raise_for_status()
    state['role'] = 'student'
    signed_url = client.get(f"/api/courses/{course['id']}/materials").json()['items'][0]['download_url']
    assert client.get(signed_url).status_code == 200
    state['role'] = 'teacher'
    assert client.post(f"/api/courses/{course['id']}/publication", json={"action":"unpublish"}).status_code == 200
    state['role'] = 'student'
    assert client.get(signed_url).status_code == 403


def test_admin_moderation_hides_course_without_deleting_records(integrated, db_session, monkeypatch):
    client, uid, state = integrated
    monkeypatch.setenv('ENGAGEMENT_CATALOG_TOKEN','engagement-catalog-secret')
    course = create(client)
    state['lessons'] = [{"id":str(uuid4()), "title":"Aula", "position":1,"duration_seconds":12}]
    client.post(f"/api/courses/{course['id']}/publication",json={"action":"publish"}).raise_for_status()
    url=f"/api/courses/{course['id']}/moderation"
    assert client.put(url,json={"decision":"hide"}).status_code==403
    state['role']='admin'
    assert client.put(url,json={"decision":"hide"}).status_code==403
    client.headers['X-Service-Token']='engagement-catalog-secret'
    hidden=client.put(url,json={"decision":"hide"})
    assert hidden.status_code==200 and hidden.json()['moderation_status']=='hidden'
    assert client.put(url,json={"decision":"hide"}).status_code==200
    del client.headers['Authorization']
    assert client.get(f"/api/courses/{course['id']}/summary").status_code==404
    assert client.get(f"/api/courses/{course['id']}").status_code==404
    assert all(item['id']!=course['id'] for item in client.get('/api/courses').json()['items'])
    client.headers['Authorization']='Bearer real'
    state['role']='teacher'
    assert client.post(f"/api/courses/{course['id']}/publication",json={"action":"publish"}).status_code==422
    state['role']='admin'
    assert client.put(url,json={"decision":"keep"}).json()['moderation_status']=='visible'
    assert client.put(url,json={"decision":"delete"}).json()['moderation_status']=='deleted'
    assert client.put(url,json={"decision":"keep"}).status_code==409
    db_session.expire_all()
    assert db_session.get(Course,UUID(course['id'])).moderation_status=='deleted'
