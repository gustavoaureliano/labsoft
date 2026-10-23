from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session, sessionmaker

from app.identity_access.api import create_router
from app.identity_access.config import Settings
from app.identity_access.models import Base, User
from app.identity_access.security import hash_password
from app.identity_access.services import ServiceError, SessionService


@pytest.fixture
def db() -> Iterator[Session]:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    with session_factory() as session:
        yield session

    engine.dispose()


def test_access_token_is_jwt_and_can_be_revoked(
    db: Session,
) -> None:
    settings = Settings(
        jwt_secret="test-signing-key-0123456789abcdef"
    )
    user = User(
        email="student@example.com",
        password_hash="unused",
    )
    db.add(user)
    db.flush()

    sessions = SessionService()
    token = sessions.create(db, user, settings)

    assert token.count(".") == 2
    assert sessions.authenticate(db, token, settings) is user

    sessions.revoke(db, token)

    with pytest.raises(ServiceError, match="Sessão ausente"):
        sessions.authenticate(db, token, settings)


def test_access_token_rejects_invalid_signature(
    db: Session,
) -> None:
    settings = Settings(
        jwt_secret="test-signing-key-0123456789abcdef"
    )
    user = User(
        email="student@example.com",
        password_hash="unused",
    )
    db.add(user)
    db.flush()

    token = SessionService().create(db, user, settings)

    with pytest.raises(ServiceError, match="Token inválido"):
        SessionService().authenticate(
            db,
            token,
            Settings(
                jwt_secret="other-signing-key-0123456789abcdef"
            ),
        )


def test_swagger_uses_oauth_password_token_endpoint() -> None:
    def get_db() -> Iterator[None]:
        yield None

    app = FastAPI()
    router = create_router(
        get_db,
        Settings(
            jwt_secret="test-signing-key-0123456789abcdef"
        ),
    )
    app.include_router(router)

    openapi = app.openapi()
    schemes = openapi["components"]["securitySchemes"]

    oauth_scheme = next(
        scheme
        for scheme in schemes.values()
        if scheme["type"] == "oauth2"
    )

    assert (
        oauth_scheme["flows"]["password"]["tokenUrl"]
        == "/api/v1/auth/token"
    )
    assert any(
        route.path == "/api/v1/auth/token"
        for route in router.routes
    )


def test_swagger_token_endpoint_issues_usable_jwt() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    settings = Settings(
        jwt_secret="test-signing-key-0123456789abcdef"
    )

    with session_factory() as db:
        db.add(
            User(
                email="student@example.com",
                password_hash=hash_password("correct horse battery"),
            )
        )
        db.commit()

    def get_db() -> Iterator[Session]:
        with session_factory() as db:
            yield db

    app = FastAPI()
    app.include_router(create_router(get_db, settings))

    with TestClient(app) as client:
        token_response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "student@example.com",
                "password": "correct horse battery",
            },
        )

        assert token_response.status_code == 200
        token_data = token_response.json()
        assert token_data["token_type"] == "bearer"
        assert token_data["access_token"].count(".") == 2

        profile_response = client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization": (
                    f"Bearer {token_data['access_token']}"
                )
            },
        )

        assert profile_response.status_code == 200
        assert profile_response.json()["email"] == "student@example.com"

    engine.dispose()
