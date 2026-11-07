from uuid import uuid4

import httpx
import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app import identity
from app.integrations import get_current_user
from app.main import app

USER_ID = str(uuid4())


def request(headers=None, method="GET"):
    return Request({"type": "http", "method": method,
                    "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]})


@pytest.fixture
def provider(monkeypatch):
    calls = []
    monkeypatch.setenv("IDENTITY_URL", "http://identity.example")
    monkeypatch.setenv("FRONTEND_ORIGIN", "https://frontend.example")
    original = httpx.Client

    def setup(handler=None):
        def handle(req):
            calls.append(req)
            if handler:
                return handler(req)
            if req.url.path.endswith("auth/me"):
                return httpx.Response(200, json={"id": USER_ID, "role": "teacher"})
            return httpx.Response(200, json={"user_id": USER_ID, "display_name": "Nome real"})
        def client(**kwargs):
            assert kwargs["timeout"] == 3 and kwargs["follow_redirects"] is False
            return original(transport=httpx.MockTransport(handle), **kwargs)
        monkeypatch.setattr(identity.httpx, "Client", client)
        return calls
    return setup


def test_cookie_is_forwarded_only_as_access_bearer(provider):
    calls = provider()
    user = get_current_user(request({"Cookie": "aprovaai_access=real; aprovaai_refresh=secret", "X-Demo-User": "aluno-demo"}))
    assert (user.id, user.role, user.name) == (USER_ID, "teacher", "Nome real")
    assert [r.url.path for r in calls] == ["/api/v1/auth/me", "/api/v1/profiles/me"]
    assert all(r.headers["authorization"] == "Bearer real" and "cookie" not in r.headers and "x-demo-user" not in r.headers for r in calls)


def test_explicit_bearer_has_precedence(provider):
    calls = provider()
    get_current_user(request({"Authorization": "Bearer explicit", "Cookie": "aprovaai_access=other"}))
    assert all(r.headers["authorization"] == "Bearer explicit" for r in calls)


@pytest.mark.parametrize("header", ["Basic wrong", "Bearer", ""])
def test_malformed_authorization_does_not_use_cookie(provider, header):
    calls = provider()
    with pytest.raises(HTTPException) as error:
        get_current_user(request({"Authorization": header, "Cookie": "aprovaai_access=valid"}))
    assert error.value.status_code == 401 and not calls


@pytest.mark.parametrize("origin", [None, "null", "https://untrusted.example"])
def test_cookie_write_rejected_before_identity_call(provider, origin):
    calls = provider()
    headers = {"Cookie": "aprovaai_access=valid"}
    if origin: headers["Origin"] = origin
    with pytest.raises(HTTPException) as error:
        get_current_user(request(headers, "POST"))
    assert error.value.status_code == 403 and not calls


def test_bearer_write_without_origin(provider):
    provider()
    assert get_current_user(request({"Authorization": "Bearer valid"}, "POST")).id == USER_ID


@pytest.mark.parametrize("status,expected", [(401,401), (403,503), (404,503), (429,503), (500,503), (302,503)])
def test_provider_error_never_falls_back_to_demo(provider, monkeypatch, status, expected):
    monkeypatch.setenv("LEARNING_DEMO_MODE", "true")
    calls = provider(lambda req: httpx.Response(status))
    with pytest.raises(HTTPException) as error:
        get_current_user(request({"Authorization": "Bearer invalid", "Cookie": "aprovaai_access=valid; aprovaai_demo_user=professor-demo"}))
    assert error.value.status_code == expected and len(calls) == 1


def test_timeout_is_dependency_failure(provider):
    def timeout(req): raise httpx.ReadTimeout("unavailable", request=req)
    provider(timeout)
    with pytest.raises(HTTPException) as error:
        get_current_user(request({"Authorization": "Bearer token"}))
    assert error.value.status_code == 503


@pytest.mark.parametrize("body", [{"id": "demo", "role": "teacher"}, {"id": USER_ID, "role": "ALUNO"}, {}])
def test_invalid_identity_response_fails_closed(provider, body):
    provider(lambda req: httpx.Response(200, json=body))
    with pytest.raises(HTTPException) as error:
        get_current_user(request({"Authorization": "Bearer token"}))
    assert error.value.status_code == 503


def test_profile_must_belong_to_identity(provider):
    provider(lambda req: httpx.Response(200, json={"id": USER_ID, "role": "teacher"} if req.url.path.endswith("auth/me") else {"user_id": str(uuid4()), "display_name": "Other"}))
    with pytest.raises(HTTPException) as error:
        get_current_user(request({"Authorization": "Bearer token"}))
    assert error.value.status_code == 503


def test_real_mode_does_not_accept_demo_identity(provider):
    calls = provider()
    with pytest.raises(HTTPException) as error:
        get_current_user(request({"X-Demo-User": "professor-demo", "Cookie": "aprovaai_demo_user=professor-demo"}))
    assert error.value.status_code == 401 and not calls


def test_upload_uses_real_teacher_identity(upload_context, provider):
    client, _, _ = upload_context
    calls = provider()
    app.dependency_overrides.pop(get_current_user)
    response = client.post("/api/media", files={"file": ("test.mp4", b"transport-fixture", "video/mp4")},
                           headers={"Cookie": "aprovaai_access=valid", "Origin": "https://frontend.example"})
    assert response.status_code == 201
    assert len(calls) == 2
