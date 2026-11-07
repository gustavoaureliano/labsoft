import pytest

from app.integrations import DemoIntegrations, get_current_user
from app.main import app


def as_user(identity):
    app.dependency_overrides[get_current_user] = lambda: DemoIntegrations.users[identity]


@pytest.mark.parametrize("identity,expected", [("aluno-demo", 200), ("aluno-demo-2", 403), ("professor-demo", 200), ("professor-demo-2", 403)])
def test_playback_and_direct_file_permissions(upload_context, identity, expected):
    client, _, _ = upload_context
    lesson = client.post("/api/learning/lessons", json={"course_id": "fisica-quantica", "title": "Aula", "position": 1}).json()
    media = client.post("/api/media", files={"file": ("a.mp4", b"video", "video/mp4")}).json()
    assert client.patch(f"/api/learning/lessons/{lesson['id']}/media", json={"media_id": media["id"]}).status_code == 200
    as_user(identity)
    assert client.get(f"/api/learning/lessons/{lesson['id']}/playback").status_code == expected
    assert client.get(f"/api/media/{media['id']}").status_code == expected
    assert client.get(f"/api/media/{media['id']}/content", headers={"Range": "bytes=0-1"}).status_code == (206 if expected == 200 else expected)


def test_unassociated_video_is_private_and_writes_require_owner(upload_context):
    client, _, _ = upload_context
    media = client.post("/api/media", files={"file": ("a.mp4", b"video", "video/mp4")}).json()
    as_user("aluno-demo")
    assert client.get(f"/api/media/{media['id']}/content").status_code == 403
    assert client.post("/api/media", files={"file": ("a.mp4", b"video", "video/mp4")}).status_code == 403
    assert client.post("/api/learning/lessons", json={"course_id": "fisica-quantica", "title": "A", "position": 1}).status_code == 403
    as_user("professor-demo-2")
    lesson = client.post("/api/learning/lessons", json={"course_id": "biologia-celular", "title": "A", "position": 1}).json()
    assert client.patch(f"/api/learning/lessons/{lesson['id']}/media", json={"media_id": media["id"]}).status_code == 403


def test_anonymous_is_denied_but_health_works(upload_context):
    client, _, _ = upload_context
    app.dependency_overrides.pop(get_current_user)
    assert client.get("/api/media/00000000-0000-0000-0000-000000000000").status_code == 401
    assert client.get("/api/health").status_code == 200
