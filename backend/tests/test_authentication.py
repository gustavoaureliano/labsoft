from __future__ import annotations

import base64
import importlib
from collections.abc import Iterator

import pytest
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.identity_access.api import create_router
from app.identity_access.config import Settings
from app.identity_access.models import (
    AuthSession,
    Base,
    EmailOutbox,
    User,
)
from app.identity_access.security import hash_password
from app.identity_access.services import (
    IdentityService,
    RateLimitService,
    ServiceError,
    SessionService,
)


def _key_pair() -> tuple[str, str]:
    private = Ed25519PrivateKey.generate()
    private_pem = private.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    public_pem = private.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private_pem, public_pem


def _settings() -> Settings:
    private_key, public_key = _key_pair()
    return Settings(
        jwt_private_key=private_key,
        jwt_public_key=public_key,
        jwt_kid="test-ed25519",
        email_encryption_key=Fernet.generate_key().decode("ascii"),
    )


class CapturingEmailSender:
    def __init__(self):
        self.messages: list[tuple[str, str, str]] = []

    def send(self, to: str, subject: str, body: str) -> None:
        self.messages.append((to, subject, body))


@pytest.fixture
def database() -> Iterator[tuple[sessionmaker, Session]]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as session:
        yield factory, session
    engine.dispose()


def _active_user(
    db: Session,
    role: str = "student",
    email: str = "student@example.com",
) -> User:
    user = User(
        email=email,
        password_hash=hash_password("correct horse battery"),
        role=role,
        is_active=True,
        status="active",
    )
    db.add(user)
    db.flush()
    return user


def test_ed25519_access_token_refresh_rotation_and_reuse_detection(
    database: tuple[sessionmaker, Session],
) -> None:
    _, db = database
    settings = _settings()
    user = _active_user(db)
    sessions = SessionService()

    initial = sessions.create(db, user, settings)
    assert initial.expires_in_seconds == 15 * 60
    assert initial.access_token.count(".") == 2
    assert sessions.authenticate(
        db,
        initial.access_token,
        settings,
    ) is user

    rotated = sessions.refresh(
        db,
        initial.refresh_token,
        settings,
    )
    db.commit()
    assert rotated.refresh_token != initial.refresh_token
    assert sessions.authenticate(
        db,
        rotated.access_token,
        settings,
    ) is user

    with pytest.raises(ServiceError, match="Reutilização"):
        sessions.refresh(db, initial.refresh_token, settings)
    assert db.get(AuthSession, initial.session_id).revoked_at is not None
    with pytest.raises(ServiceError, match="Sessão ausente"):
        sessions.authenticate(db, rotated.access_token, settings)


def test_jwt_rejects_wrong_audience_and_wrong_key(
    database: tuple[sessionmaker, Session],
) -> None:
    _, db = database
    settings = _settings()
    user = _active_user(db)
    token = SessionService().create(db, user, settings).access_token

    with pytest.raises(ServiceError, match="Token inválido"):
        SessionService().authenticate(
            db,
            token,
            _settings(),
        )

    invalid_audience = Settings(
        jwt_private_key=settings.jwt_private_key,
        jwt_public_key=settings.jwt_public_key,
        jwt_kid=settings.jwt_kid,
        jwt_audience="another-api",
    )
    with pytest.raises(ServiceError, match="Token inválido"):
        SessionService().authenticate(
            db,
            token,
            invalid_audience,
        )


def test_role_change_revokes_existing_sessions(
    database: tuple[sessionmaker, Session],
) -> None:
    _, db = database
    settings = _settings()
    user = _active_user(db)
    sessions = SessionService()
    tokens = sessions.create(db, user, settings)
    db.flush()

    updated = IdentityService().set_role(
        db,
        user.id,
        "teacher",
    )
    db.commit()

    assert updated.role == "teacher"
    with pytest.raises(ServiceError, match="Sessão ausente"):
        sessions.authenticate(db, tokens.access_token, settings)


def test_email_verification_is_one_time_and_login_waits_for_it(
    database: tuple[sessionmaker, Session],
) -> None:
    factory, db = database
    settings = _settings()
    app = FastAPI()

    def get_db() -> Iterator[Session]:
        with factory() as request_db:
            yield request_db

    app.include_router(
        create_router(
            get_db,
            settings,
            email_sender=CapturingEmailSender(),
        )
    )
    client = TestClient(app)

    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new@example.com",
            "display_name": "New Student",
            "password": "correct horse battery 7",
        },
    )
    assert registration.status_code == 201
    assert registration.json()["role"] == "student"
    assert client.post(
        "/api/v1/auth/login",
        json={
            "email": "new@example.com",
            "password": "correct horse battery 7",
        },
    ).status_code == 401

    queued = db.query(EmailOutbox).filter_by(
        recipient="new@example.com"
    ).one()
    token = Fernet(
        settings.email_encryption_key.encode("ascii")
    ).decrypt(queued.encrypted_token.encode("ascii")).decode()

    verified = client.post(
        "/api/v1/auth/verify-email",
        json={"token": token},
    )
    assert verified.status_code == 200
    assert client.post(
        "/api/v1/auth/verify-email",
        json={"token": token},
    ).status_code == 400
    assert client.post(
        "/api/v1/auth/login",
        json={
            "email": "new@example.com",
            "password": "correct horse battery 7",
        },
    ).status_code == 200


def test_login_issues_refresh_cookie_and_refresh_rotates(
    database: tuple[sessionmaker, Session],
) -> None:
    factory, db = database
    settings = _settings()
    _active_user(db)
    db.commit()

    def get_db() -> Iterator[Session]:
        with factory() as request_db:
            yield request_db

    app = FastAPI()
    app.include_router(create_router(get_db, settings))
    client = TestClient(app)

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "student@example.com",
            "password": "correct horse battery",
        },
    )
    assert login.status_code == 200
    assert login.headers["cache-control"] == "no-store"
    assert "HttpOnly" in login.headers["set-cookie"]
    old_refresh = client.cookies.get("aprovaai_refresh")

    refresh = client.post(
        "/api/v1/auth/refresh",
        headers={"Origin": settings.frontend_origin},
    )
    assert refresh.status_code == 200
    assert refresh.json()["access_token"] != login.json()["access_token"]
    assert client.cookies.get("aprovaai_refresh") != old_refresh


def test_openapi_uses_bearer_not_password_grant() -> None:
    settings = _settings()

    def get_db() -> Iterator[None]:
        yield None

    app = FastAPI()
    app.include_router(create_router(get_db, settings))
    schema = app.openapi()
    schemes = schema["components"]["securitySchemes"]

    assert any(
        scheme["type"] == "http"
        and scheme["scheme"] == "bearer"
        for scheme in schemes.values()
    )
    assert not any(
        scheme["type"] == "oauth2"
        for scheme in schemes.values()
    )
    assert "/api/v1/auth/token" not in schema["paths"]


def test_admin_docs_tokens_require_current_admin_and_live_session(
    database: tuple[sessionmaker, Session],
) -> None:
    _, db = database
    settings = _settings()
    sessions = SessionService()
    admin = _active_user(db, "admin", "admin@example.com")
    admin_session = sessions.create(db, admin, settings)
    docs_token = sessions.create_admin_docs_token(
        admin,
        admin_session.session_id,
        settings,
    )
    assert sessions.authenticate_admin_docs(
        db,
        docs_token,
        settings,
    ) is admin

    student = _active_user(db, "student", "another@example.com")
    student_session = sessions.create(db, student, settings)
    student_docs_token = sessions.create_admin_docs_token(
        student,
        student_session.session_id,
        settings,
    )
    with pytest.raises(ServiceError, match="restrita"):
        sessions.authenticate_admin_docs(
            db,
            student_docs_token,
            settings,
        )

    sessions.revoke_session(db, admin_session.session_id)
    with pytest.raises(ServiceError, match="restrita"):
        sessions.authenticate_admin_docs(
            db,
            docs_token,
            settings,
        )


def test_database_rate_limit_tracks_ip_and_identity_keys(
    database: tuple[sessionmaker, Session],
) -> None:
    _, db = database
    limiter = RateLimitService()

    assert limiter.consume(db, "login:ip:127.0.0.1", 2, 60)
    assert limiter.consume(db, "login:ip:127.0.0.1", 2, 60)
    assert not limiter.consume(db, "login:ip:127.0.0.1", 2, 60)


def test_swagger_and_openapi_require_admin_docs_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_key, public_key = _key_pair()

    def encode(value: str) -> str:
        return base64.urlsafe_b64encode(
            value.encode()
        ).decode().rstrip("=")

    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv(
        "AA_JWT_PRIVATE_KEY_B64",
        encode(private_key),
    )
    monkeypatch.setenv(
        "AA_JWT_PUBLIC_KEY_B64",
        encode(public_key),
    )
    monkeypatch.setenv("AA_JWT_KID", "docs-test")
    monkeypatch.setenv(
        "AA_EMAIL_ENCRYPTION_KEY",
        Fernet.generate_key().decode(),
    )
    monkeypatch.setenv("AA_COOKIE_SECURE", "false")
    monkeypatch.setenv("AA_FRONTEND_ORIGIN", "http://testserver")

    main = importlib.import_module("app.main")
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory.begin() as db:
        admin = User(
            email="admin@example.com",
            password_hash=hash_password("correct horse battery"),
            role="admin",
            is_active=True,
            status="active",
        )
        db.add(admin)
        db.flush()

    def get_test_db() -> Iterator[Session]:
        with factory() as db:
            yield db

    main.app.dependency_overrides[main.get_db] = get_test_db
    try:
        client = TestClient(main.app, follow_redirects=False)
        assert client.get("/docs").status_code == 303
        assert client.get("/openapi.json").status_code == 401
        assert client.get("/redoc").status_code == 404

        login = client.post(
            "/admin/login",
            headers={"Origin": "http://testserver"},
            data={
                "email": "admin@example.com",
                "password": "correct horse battery",
            },
        )
        assert login.status_code == 303
        assert "aprovaai_admin_docs" in login.cookies
        assert client.get("/docs").status_code == 200
        schema_response = client.get("/openapi.json")
        assert schema_response.status_code == 200
        assert schema_response.headers["cache-control"] == "no-store"
    finally:
        main.app.dependency_overrides.clear()
        engine.dispose()
