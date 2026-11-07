import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.integrations import DemoIntegrations, get_current_user, get_integrations
from app.learning.models import Lesson
from app.seed import seed_lessons


def test_development_mode_is_explicit(monkeypatch):
    monkeypatch.delenv("LEARNING_DEMO_MODE", raising=False)
    with pytest.raises(HTTPException) as error:
        get_integrations()
    assert error.value.status_code == 503
    monkeypatch.setenv("LEARNING_DEMO_MODE", "true")
    assert isinstance(get_integrations(), DemoIntegrations)


def test_identity_and_access_contracts():
    integrations = DemoIntegrations()
    request = Request({"type": "http", "headers": [(b"x-demo-user", b"aluno-demo")]})
    assert get_current_user(request, integrations).id == "aluno-demo"
    assert integrations.user("missing") is None
    assert integrations.course("missing") is None
    assert integrations.has_access("aluno-demo", "fisica-quantica")
    assert not integrations.has_access("aluno-demo-2", "fisica-quantica")
    assert integrations.course("fisica-quantica").owner_id != "professor-demo-2"
    with pytest.raises(HTTPException) as error:
        get_current_user(Request({"type": "http", "headers": []}), integrations)
    assert error.value.status_code == 401


def test_seed_is_repeatable_and_preserves_existing_lessons(upload_context):
    _, sessions, _ = upload_context
    with sessions() as session:
        session.add(Lesson(id="user-lesson", course_id="fisica-quantica", title="Minha aula", position=1))
        session.commit()
        assert seed_lessons(session) == 3
        assert seed_lessons(session) == 0
        assert session.get(Lesson, "user-lesson").title == "Minha aula"
