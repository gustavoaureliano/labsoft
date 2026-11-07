"""The real adapter must not trust demo identity or expose another student's data."""
from uuid import uuid4

import httpx
import pytest

from app import remote
from app.integrations import get_integrations
from app.main import app


@pytest.fixture
def integrated(test_context, monkeypatch):
    client, _, _ = test_context
    app.dependency_overrides.pop(get_integrations)
    ids = [str(uuid4()), str(uuid4())]
    course, lesson = str(uuid4()), str(uuid4())
    state = {"allowed": {ids[0]: True, ids[1]: True}, "down": False, "calls": []}
    for key, url in {"IDENTITY_URL": "http://identity", "CATALOG_URL": "http://catalog",
                     "LEARNING_URL": "http://learning", "ACCESS_URL": "http://access",
                     "FRONTEND_ORIGIN": "http://testserver"}.items():
        monkeypatch.setenv(key, url)
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
                return httpx.Response(200, json={"id": user_id, "role": "student"})
            return httpx.Response(200, json={"user_id": user_id, "display_name": f"Aluno {actor}"})
        if req.url.host == "catalog":
            return httpx.Response(200, json={"id": course, "teacher_id": str(uuid4()),
                                              "title": "Física", "teacher_name": "Professora", "status": "published"})
        if req.url.host == "learning":
            if req.url.path.endswith("/summary"):
                return httpx.Response(200 if state["allowed"][user_id] else 403,
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
