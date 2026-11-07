import os
from types import SimpleNamespace
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "sqlite://")

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app import auth, db as database
from app.main import app, Subscription


@pytest.fixture
def api(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path}/subscription.sqlite", connect_args={"check_same_thread": False})
    engine = engine.execution_options(schema_translate_map={"subscription": None})
    database.Base.metadata.create_all(engine)
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setenv("IDENTITY_URL", "http://identity")
    monkeypatch.setenv("CATALOG_URL", "http://catalog")
    monkeypatch.setenv("FRONTEND_ORIGIN", "http://testserver")
    users = {"student-a": uuid4(), "student-b": uuid4(), "teacher": uuid4()}
    course_id = uuid4()
    state = {"id": str(course_id), "status": "published", "access_type": "free", "price": "0.00"}
    calls = []
    original = httpx.Client

    def handle(request):
        calls.append(request)
        assert "cookie" not in request.headers
        value = request.headers["authorization"].split()[1]
        if request.url.host == "identity":
            if value not in users: return httpx.Response(401)
            return httpx.Response(200, json={"id": str(users[value]), "role": "teacher" if value == "teacher" else "student"})
        if state.get("http_status"): return httpx.Response(state["http_status"])
        if str(course_id) not in request.url.path: return httpx.Response(404)
        return httpx.Response(200, json=state)

    monkeypatch.setattr(auth.httpx, "Client", lambda **kw: original(transport=httpx.MockTransport(handle), **kw))
    def session():
        with Session(engine) as db: yield db
    app.dependency_overrides[database.get_session] = session
    try:
        with TestClient(app) as client:
            client.headers["Authorization"] = "Bearer student-a"
            yield SimpleNamespace(client=client, engine=engine, users=users, course_id=course_id, state=state, calls=calls)
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
