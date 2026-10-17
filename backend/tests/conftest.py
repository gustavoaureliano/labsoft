import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from app.database import Base, get_session
from app.main import app
from app.media import storage
from app.integrations import DemoIntegrations, get_integrations, get_current_user


@pytest.fixture
def upload_context(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'test.db'}")
    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    root = tmp_path / "storage"
    monkeypatch.setattr(storage, "STORAGE_ROOT", root)

    def test_session():
        with sessions() as session:
            yield session

    app.dependency_overrides[get_session] = test_session
    app.dependency_overrides[get_integrations] = DemoIntegrations
    app.dependency_overrides[get_current_user] = lambda: DemoIntegrations.users["professor-demo"]
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            yield client, sessions, root
    finally:
        app.dependency_overrides.pop(get_session, None)
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_integrations, None)
        engine.dispose()
