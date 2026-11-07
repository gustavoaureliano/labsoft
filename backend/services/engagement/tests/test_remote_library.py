"""The real adapter must not trust demo identity or expose another student's data."""
from uuid import uuid4
import json
import os

import httpx
import pytest

from app import remote
from app.integrations import get_integrations
from app.main import app


@pytest.fixture
def integrated(test_context, monkeypatch):
    client, _, _ = test_context
    app.dependency_overrides.pop(get_integrations)
    ids = [str(uuid4()) for _ in range(4)]
    course, lesson = str(uuid4()), str(uuid4())
    state = {"allowed": {ids[0]: True, ids[1]: True}, "down": False, "calls": [],
             "audit": {}, "audit_down": False, "moderation_status": "visible"}
    for key, url in {"IDENTITY_URL": "http://identity", "CATALOG_URL": "http://catalog",
                     "LEARNING_URL": "http://learning", "ACCESS_URL": "http://access",
                     "FRONTEND_ORIGIN": "http://testserver"}.items():
        monkeypatch.setenv(key, url)
    monkeypatch.setenv('INTERNAL_SERVICE_TOKEN','shared-internal-test-secret')
    original = httpx.Client

    def respond(req):
        state["calls"].append(req)
        assert "cookie" not in req.headers and "x-demo-user" not in req.headers
        actor = int(req.headers["authorization"].removeprefix("Bearer "))
        user_id = ids[actor]
        if state["down"]:
            return httpx.Response(503)
        if req.url.host == "identity":
            if req.url.path.endswith("/auth/me"):
                return httpx.Response(200, json={"id": user_id, "role": "admin" if actor == 3 else "teacher" if actor == 2 else "student"})
            if req.method == 'POST' and req.url.path.endswith('/admin/audit/moderation'):
                if state['audit_down']:return httpx.Response(503)
                assert req.headers['x-service-token']==os.environ['INTERNAL_SERVICE_TOKEN']
                body=json.loads(req.content)
                state['audit'].setdefault(body['operation_id'],body)
                return httpx.Response(201,json={'recorded':True,'audit_id':body['operation_id']})
            return httpx.Response(200, json={"user_id": user_id, "display_name": f"Aluno {actor}"})
        if req.url.host == "catalog":
            if req.method == 'PUT':
                assert req.headers['x-service-token']==os.environ['INTERNAL_SERVICE_TOKEN']
                state['moderation_status']={'keep':'visible','hide':'hidden','delete':'deleted'}[json.loads(req.content)['decision']]
                return httpx.Response(200,json={'moderation_status':state['moderation_status']})
            return httpx.Response(200, json={"id": course, "teacher_id": ids[2],
                                              "title": "Física", "teacher_name": "Professora", "status": "published",
                                              "moderation_status":state['moderation_status']})
        if req.url.host == "learning":
            if req.method == 'PUT':
                assert req.headers['x-service-token']==os.environ['INTERNAL_SERVICE_TOKEN']
                state['moderation_status']={'keep':'visible','hide':'hidden','delete':'deleted'}[json.loads(req.content)['decision']]
                return httpx.Response(200,json={'moderation_status':state['moderation_status']})
            if req.url.path.endswith("/summary"):
                return httpx.Response(200 if actor in (2,3) or state["allowed"][user_id] else 403,
                                      json={"id": lesson, "course_id": course, "title": "Aula real", "position": 1})
        if req.url.host == "access":
            return httpx.Response(200, json={"user_id": user_id, "course_id": course,
                                              "allowed": state["allowed"][user_id]})
        return httpx.Response(503)

    monkeypatch.setattr(remote.httpx, "Client", lambda **kw: original(transport=httpx.MockTransport(respond), **kw))
    yield client, ids, course, lesson, state


def headers(actor=0, method="POST"):
    result = {"Authorization": f"Bearer {actor}", "X-Demo-User": "professor-demo"}
    if method != "GET": result["Origin"] = "http://testserver"
    return result


def test_history_favorites_playlists_private_and_ordered(integrated):
    client, ids, course, lesson, state = integrated
    created = client.post("/api/library/history/"+lesson, headers=headers())
    assert created.status_code == 200, created.text
    assert created.json()["course_id"] == course
    assert client.post("/api/library/favorites/"+lesson, headers=headers()).status_code == 201
    playlist = client.post("/api/library/playlists", headers=headers(), json={"name": "Revisão"})
    assert playlist.status_code == 201, playlist.text
    playlist_id = playlist.json()["id"]
    saved = client.put(f"/api/library/playlists/{playlist_id}/lessons", headers=headers(), json={"lesson_ids": [lesson]})
    assert saved.status_code == 200, saved.text
    playback = client.get(f"/api/library/playlists/{playlist_id}/playback/{lesson}", headers=headers(method="GET"))
    assert playback.status_code == 200 and playback.json()["sequence"] == [lesson]
    assert client.get("/api/library/history", headers=headers(1, "GET")).json() == []
    assert client.get("/api/library/favorites", headers=headers(1, "GET")).json() == []
    assert client.get("/api/library/playlists", headers=headers(1, "GET")).json() == []
    denied = client.put(f"/api/library/playlists/{playlist_id}/lessons", headers=headers(1), json={"lesson_ids": [lesson]})
    assert denied.status_code == 404
    assert all(req.headers["authorization"] in {"Bearer 0", "Bearer 1"} for req in state["calls"])


def test_loss_of_access_denies_new_interactions(integrated):
    client, ids, course, lesson, state = integrated
    state["allowed"][ids[0]] = False
    assert client.post("/api/library/history/"+lesson, headers=headers()).status_code in (403, 404)
    assert client.post("/api/library/favorites/"+lesson, headers=headers()).status_code in (403, 404)
    assert client.get("/api/library/history", headers=headers(method="GET")).status_code == 200


def test_dependency_failure_is_not_an_empty_library(integrated):
    client, _, _, _, state = integrated
    state["down"] = True
    result = client.get("/api/library/history", headers=headers(method="GET"))
    assert result.status_code == 503


@pytest.mark.parametrize("method", ["POST", "GET"])
def test_real_mode_rejects_demo_headers_without_credential(integrated, method):
    client, _, _, lesson, _ = integrated
    result = client.request(method, "/api/library/history" if method == "GET" else f"/api/library/history/{lesson}",
                            headers={"X-Demo-User": "aluno-demo", "Cookie": "aprovaai_demo_user=aluno-demo"})
    assert result.status_code == 401


def test_cookie_write_requires_origin(integrated):
    client, _, _, lesson, _ = integrated
    result = client.post("/api/library/history/"+lesson, headers={"Cookie": "aprovaai_access=0"})
    assert result.status_code == 403


def test_demo_reset_is_disabled_with_real_identity(integrated):
    client, _, _, _, _ = integrated
    assert client.post("/api/testing/reset", headers=headers()).status_code == 404


def test_personal_library_responses_are_not_publicly_cached(integrated):
    client, _, _, _, _ = integrated
    response = client.get("/api/library/history", headers=headers(method="GET"))
    assert response.status_code == 200
    assert response.headers["cache-control"] == "private, no-store"


def test_notes_comments_and_ratings_use_real_lesson_access(integrated):
    client, ids, _, lesson, state = integrated
    note = f"/api/interactions/lessons/{lesson}/note"
    assert client.put(note, headers=headers(), json={"content":"Minha nota privada"}).status_code == 200
    assert client.get(note, headers=headers(method="GET")).json()["content"] == "Minha nota privada"
    assert client.get(note, headers=headers(1,"GET")).json()["content"] == ""
    comment = client.post(f"/api/interactions/lessons/{lesson}/comments", headers=headers(), json={"content":"Aula muito boa"})
    assert comment.status_code == 201 and comment.json()["author_id"] == ids[0]
    rating = client.put(f"/api/interactions/ratings/{lesson}", headers=headers(), json={"target_type":"lesson","stars":5})
    assert rating.status_code == 200 and rating.json()["student_stars"] == 5
    state["allowed"][ids[0]] = False
    assert client.put(note, headers=headers(), json={"content":"Não posso escrever"}).status_code in (403,404)
    assert client.post(f"/api/interactions/lessons/{lesson}/comments", headers=headers(), json={"content":"Sem acesso"}).status_code in (403,404)
    assert client.put(f"/api/interactions/ratings/{lesson}", headers=headers(), json={"stars":1}).status_code in (403,404)


def test_student_question_teacher_answer_and_private_notifications(integrated):
    client, ids, course, lesson, state = integrated
    sent = client.post("/api/questions", headers=headers(), json={"course_id":course,"lesson_id":lesson,"prompt":"Pode explicar esta aula?"})
    assert sent.status_code == 201, sent.text
    question_id = sent.json()["id"]
    assert sent.json()["teacher_id"] == ids[2]
    assert client.get("/api/questions/me", headers=headers(1,"GET")).json() == []
    assert client.get("/api/questions/teacher", headers=headers(2,"GET")).json()[0]["id"] == question_id
    assert client.get("/api/notifications", headers=headers(2,"GET")).json()[0]["kind"] == "new_question"
    assert client.get("/api/notifications", headers=headers(1,"GET")).json() == []
    assert client.patch(f"/api/questions/{question_id}/answer", headers=headers(1), json={"answer":"Não sou o professor"}).status_code == 403
    answer = client.patch(f"/api/questions/{question_id}/answer", headers=headers(2), json={"answer":"Vamos revisar juntos."})
    assert answer.status_code == 200 and answer.json()["status"] == "answered"
    assert client.get("/api/questions/me", headers=headers(method="GET")).json()[0]["answer"] == "Vamos revisar juntos."
    notice = client.get("/api/notifications", headers=headers(method="GET")).json()[0]
    assert notice["kind"] == "question_answered"
    assert client.patch(f"/api/notifications/{notice['id']}/read", headers=headers(1)).status_code == 404
    assert client.patch(f"/api/notifications/{notice['id']}/read", headers=headers()).json()["is_read"] is True


def test_question_refuses_unenrolled_student(integrated):
    client, ids, course, lesson, state = integrated
    state["allowed"][ids[0]] = False
    assert client.post("/api/questions", headers=headers(), json={"course_id":course,"lesson_id":lesson,"prompt":"Sem acesso"}).status_code == 403


@pytest.mark.parametrize('item_type', ['lesson','course'])
def test_admin_applies_owner_decision_and_records_one_audit(integrated, item_type):
    client, ids, course, lesson, state = integrated
    item_id = lesson if item_type == 'lesson' else course
    report = client.post('/api/moderation/reports',headers=headers(),json={
        'item_type':item_type,'item_id':item_id,'reason':'Problema observado'})
    assert report.status_code == 201, report.text
    admin=headers(3)
    queue=client.get('/api/moderation/queue',headers=headers(3,'GET'))
    assert queue.status_code == 200 and len(queue.json()) == 1
    url=f'/api/moderation/queue/{item_id}/decision'
    body={'item_type':item_type,'decision':'hide','justification':'Revisão necessária'}
    assert client.post(url,headers=headers(),json=body).status_code == 403
    hidden=client.post(url,headers=admin,json=body)
    assert hidden.status_code == 200, hidden.text
    assert hidden.json()['status']=='hidden' and hidden.json()['audit_recorded'] is True
    assert state['moderation_status']=='hidden' and len(state['audit'])==1
    assert client.post(url,headers=admin,json=body).status_code == 200
    assert len(state['audit'])==1
    restored=client.post(url,headers=admin,json={**body,'decision':'keep'})
    assert restored.status_code==200 and state['moderation_status']=='visible'
    assert len(state['audit'])==2


def test_failed_audit_leaves_case_pending_for_retry(integrated):
    client, ids, course, lesson, state=integrated
    reported=client.post('/api/moderation/reports',headers=headers(),json={
        'item_type':'lesson','item_id':lesson,'reason':'Conteúdo indevido'})
    assert reported.status_code==201
    state['audit_down']=True
    url=f'/api/moderation/queue/{lesson}/decision'
    decision={'item_type':'lesson','decision':'hide','justification':'Revisão necessária'}
    assert client.post(url,headers=headers(3),json=decision).status_code==503
    assert state['moderation_status']=='hidden'
    assert len(client.get('/api/moderation/queue',headers=headers(3,'GET')).json())==1
    state['audit_down']=False
    assert client.post(url,headers=headers(3),json=decision).status_code==200
    assert len(state['audit'])==1
