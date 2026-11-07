from contextlib import contextmanager
import json
import os
from pathlib import Path
import tempfile
import unittest
from urllib.parse import urlencode, urlsplit

import anyio
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["LEARNING_DEMO_MODE"] = "true"

import app.migrations_models_loader  # noqa: F401
from app.database import Base, get_session
from app.integrations import DemoIntegrations, get_integrations
from app.main import app


class _ASGIResponse:
    def __init__(self, status_code: int, headers: dict[str, str], body: bytes):
        self.status_code = status_code
        self.headers = headers
        self.content = body
        self.text = body.decode("utf-8", errors="replace")

    def json(self):
        return json.loads(self.text) if self.text else None


class ASGITestClient:
    """Lightweight synchronous ASGI client powered by anyio (no external httpx dependency required)."""

    def __init__(self, asgi_app):
        self.app = asgi_app

    def request(
        self,
        method: str,
        url: str,
        *,
        json_body=None,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ) -> _ASGIResponse:
        parsed = urlsplit(url)
        path = parsed.path or "/"
        query_string = parsed.query
        if params:
            extra_q = urlencode(params)
            query_string = f"{query_string}&{extra_q}" if query_string else extra_q

        raw_body = b""
        req_headers = [(b"host", b"testserver")]
        if headers:
            for k, v in headers.items():
                req_headers.append((k.lower().encode("latin-1"), v.encode("latin-1")))
        if json_body is not None:
            raw_body = json.dumps(json_body).encode("utf-8")
            req_headers.append((b"content-type", b"application/json"))
            req_headers.append((b"content-length", str(len(raw_body)).encode("latin-1")))

        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": method.upper(),
            "scheme": "http",
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": query_string.encode("ascii"),
            "headers": req_headers,
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
        }

        status_code = 500
        resp_headers: dict[str, str] = {}
        chunks: list[bytes] = []
        body_sent = False

        async def receive():
            nonlocal body_sent
            if not body_sent:
                body_sent = True
                return {"type": "http.request", "body": raw_body, "more_body": False}
            return {"type": "http.disconnect"}

        async def send(message):
            nonlocal status_code, resp_headers
            if message["type"] == "http.response.start":
                status_code = message["status"]
                resp_headers = {
                    k.decode("latin-1").lower(): v.decode("latin-1")
                    for k, v in message.get("headers", [])
                }
            elif message["type"] == "http.response.body":
                chunks.append(message.get("body", b""))

        async def _run():
            await self.app(scope, receive, send)

        anyio.run(_run)
        return _ASGIResponse(status_code, resp_headers, b"".join(chunks))

    def get(self, url: str, *, headers: dict[str, str] | None = None, params=None):
        return self.request("GET", url, headers=headers, params=params)

    def post(self, url: str, *, json=None, headers: dict[str, str] | None = None):
        return self.request("POST", url, json_body=json, headers=headers)

    def put(self, url: str, *, json=None, headers: dict[str, str] | None = None):
        return self.request("PUT", url, json_body=json, headers=headers)

    def patch(self, url: str, *, json=None, headers: dict[str, str] | None = None):
        return self.request("PATCH", url, json_body=json, headers=headers)

    def delete(self, url: str, *, headers: dict[str, str] | None = None):
        return self.request("DELETE", url, headers=headers)


@contextmanager
def create_test_context():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test.db"
        engine = create_engine(
            f"sqlite+pysqlite:///{db_path}",
            connect_args={"check_same_thread": False},
        )

        @event.listens_for(engine, "connect")
        def enable_foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

        Base.metadata.create_all(engine)
        sessions = sessionmaker(bind=engine)
        integrations = DemoIntegrations()

        def override_session():
            with sessions() as session:
                yield session

        app.dependency_overrides[get_session] = override_session
        app.dependency_overrides[get_integrations] = lambda: integrations
        try:
            client = ASGITestClient(app)
            yield client, sessions, integrations
        finally:
            app.dependency_overrides.pop(get_session, None)
            app.dependency_overrides.pop(get_integrations, None)
            engine.dispose()


try:
    import pytest

    @pytest.fixture
    def test_context():
        with create_test_context() as ctx:
            yield ctx
except ImportError:
    pass


class BackendTestCase(unittest.TestCase):
    def setUp(self):
        self._ctx_manager = create_test_context()
        self.test_context = self._ctx_manager.__enter__()

    def tearDown(self):
        self._ctx_manager.__exit__(None, None, None)
