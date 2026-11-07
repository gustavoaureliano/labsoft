from __future__ import annotations

import base64
import importlib
from collections.abc import Callable, Iterator
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import jwt

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

from app.services.identity_access.config import Settings
from app.services.identity_access.models import (
    AuditEvent,
    AuthSession,
    EmailToken,
    MediaItem,
    Notification,
    PasswordReset,
    Profile,
    RateLimitBucket,
    RefreshToken,
    utcnow,
    Base,
    EmailOutbox,
    User,
)
from app.services.identity_access.security import hash_password
from app.services.identity_access.services import (
    EmailOutboxService,
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
        email_flows_enabled=True,
    )


class CapturingEmailSender:
    def __init__(self):
        self.messages: list[tuple[str, str, str]] = []

    def send(self, to: str, subject: str, body: str) -> None:
        self.messages.append((to, subject, body))


@pytest.fixture
def create_router(monkeypatch: pytest.MonkeyPatch) -> Callable:
    # A main agora declara as rotas e inicializa a aplicação ao ser importada.
    settings = _settings()
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    with monkeypatch.context() as startup_patch:
        startup_patch.setattr(
            Settings, "from_env", classmethod(lambda cls: settings)
        )
        main = importlib.import_module("app.main")
    return main.create_router


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
    create_router: Callable,
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
        headers={"Origin": settings.frontend_origin},
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
        headers={"Origin": settings.frontend_origin},
        json={
            "email": "new@example.com",
            "password": "correct horse battery 7",
        },
    ).status_code == 200


def test_registration_without_email_flow_is_immediately_usable(api):
    settings = replace(api.settings, email_flows_enabled=False, email_encryption_key="")
    app = FastAPI()
    app.include_router(api.create_router(api.get_db, settings))
    with TestClient(app) as client:
        created = _register(client)
        assert created.status_code == 201, created.text
        user = api.db.get(User, created.json()["id"])
        assert user.status == "active" and user.is_active and user.verified_at is None
        assert api.db.get(Profile, user.id) is not None
        assert api.db.query(EmailOutbox).count() == 0
        assert api.db.query(EmailToken).count() == 0
        assert client.post("/api/v1/auth/login", headers={"Origin": settings.frontend_origin},
                           json={"email": "new@example.com", "password": "correct horse battery 7"}).status_code == 200
        assert _register(client).status_code == 409
        for path, payload in (("verify-email", {"token": "x" * 43}),
                              ("resend-verification", {"email": "new@example.com"}),
                              ("forgot-password", {"email": "new@example.com"}),
                              ("password-recovery/request", {"email": "new@example.com"}),
                              ("reset-password", {"token": "x" * 43, "new_password": "correct horse battery 8"}),
                              ("password-recovery/confirm", {"token": "x" * 43, "new_password": "correct horse battery 8"})):
            assert client.post(f"/api/v1/auth/{path}", json=payload).status_code == 404
        assert api.db.query(PasswordReset).count() == 0


def test_login_issues_refresh_cookie_and_refresh_rotates(
    create_router: Callable,
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
        headers={"Origin": settings.frontend_origin},
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


def test_api_uses_database_role_for_authorization_and_revokes_after_change(
    create_router: Callable,
    database: tuple[sessionmaker, Session],
) -> None:
    factory, db = database
    settings = _settings()
    student = _active_user(db)
    admin = _active_user(
        db,
        role="admin",
        email="admin@example.com",
    )
    sessions = SessionService()
    student_tokens = sessions.create(db, student, settings)
    admin_tokens = sessions.create(db, admin, settings)
    db.commit()

    def get_db() -> Iterator[Session]:
        with factory() as request_db:
            yield request_db

    app = FastAPI()
    app.include_router(create_router(get_db, settings))
    client = TestClient(app)
    student_headers = {
        "Authorization": f"Bearer {student_tokens.access_token}"
    }
    admin_headers = {
        "Authorization": f"Bearer {admin_tokens.access_token}"
    }

    identity = client.get("/api/v1/auth/me", headers=student_headers)
    assert identity.status_code == 200
    assert identity.json()["role"] == "student"
    assert client.get(
        "/api/v1/auth/test/teacher",
        headers=student_headers,
    ).status_code == 403
    assert client.patch(
        f"/api/v1/admin/users/{student.id}/role",
        headers=student_headers,
        json={"role": "admin"},
    ).status_code == 403

    changed = client.patch(
        f"/api/v1/admin/users/{student.id}/role",
        headers=admin_headers,
        json={"role": "teacher"},
    )
    assert changed.status_code == 200
    assert changed.json()["role"] == "teacher"
    assert client.get(
        "/api/v1/auth/me",
        headers=student_headers,
    ).status_code == 401


def test_openapi_uses_bearer_not_password_grant(create_router: Callable) -> None:
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

    main = importlib.reload(importlib.import_module("app.main"))
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


# Integração das rotas: banco e arquivos isolados, sem envio externo de e-mail.
@pytest.fixture
def api(create_router: Callable, database, tmp_path: Path) -> Iterator[SimpleNamespace]:
    factory, db = database
    settings = replace(_settings(), media_root=tmp_path / "uploads", max_document_bytes=1024)

    def get_db():
        with factory() as request_db:
            yield request_db

    app = FastAPI()
    app.include_router(create_router(get_db, settings, CapturingEmailSender()))

    def account(role="student", email=None):
        email = email or f"{role}-{db.query(User).count()}@example.com"
        user = _active_user(db, role, email)
        user.verified_at = utcnow()
        db.add(Profile(user_id=user.id, display_name="Test User", preferences={}))
        tokens = SessionService().create(db, user, settings)
        db.commit()
        return user, tokens, {"Authorization": f"Bearer {tokens.access_token}"}

    def queued_token(purpose, user_id):
        db.expire_all()
        queued = db.query(EmailOutbox).filter_by(purpose=purpose, user_id=user_id).order_by(
            EmailOutbox.created_at.desc()
        ).first()
        assert queued is not None
        return Fernet(settings.email_encryption_key.encode()).decrypt(
            queued.encrypted_token.encode()
        ).decode()

    with TestClient(app) as client:
        yield SimpleNamespace(
            client=client, db=db, settings=settings, account=account,
            queued_token=queued_token, get_db=get_db, create_router=create_router,
        )


def _register(client, **overrides):
    body = {"email": "new@example.com", "display_name": "New Student",
            "password": "correct horse battery 7"}
    body.update(overrides)
    return client.post("/api/v1/auth/register", json=body)


def _upload(api, headers, filename="document.pdf", content=b"%PDF-1.7\nexample"):
    return api.client.post("/api/v1/media/documents", headers=headers,
                           files={"file": (filename, content, "application/octet-stream")})


def _application(document_ids):
    return {"legal_name": "Test Teacher", "professional_summary": "Experience teaching mathematics for ten years.",
            "expertise": "Mathematics", "document_ids": document_ids}


@pytest.mark.parametrize("method,path", [
    ("GET", "/auth/me"), ("GET", "/auth/sessions"),
    ("DELETE", "/auth/sessions/unknown"), ("POST", "/auth/logout-all"),
    ("GET", "/auth/test/teacher"), ("PATCH", "/admin/users/unknown/role"),
    ("PATCH", "/admin/users/unknown/status"), ("GET", "/profiles/me"),
    ("PATCH", "/profiles/me"), ("POST", "/media/documents"),
    ("GET", "/media/documents/unknown"), ("POST", "/teacher-applications"),
    ("GET", "/teacher-applications/me"), ("GET", "/notifications/me"),
    ("PATCH", "/notifications/unknown/read"),
])
def test_protected_routes_require_authentication(api, method, path):
    response = api.client.request(method, "/api/v1" + path)
    assert response.status_code == 401


@pytest.mark.parametrize("overrides", [
    {"password": "short1"}, {"password": "onlyletterslong"},
    {"password": "123456789012"}, {"email": "invalid"},
    {"display_name": "x"}, {"role": "admin"},
])
def test_registration_rejects_invalid_input_and_privilege_injection(api, overrides):
    assert _register(api.client, **overrides).status_code == 422
    assert api.db.query(User).count() == 0
    assert api.db.query(EmailOutbox).count() == 0


def test_registration_normalizes_email_creates_profile_and_rejects_duplicate(api):
    created = _register(api.client, email="MixedCase@EXAMPLE.COM")
    assert created.status_code == 201
    assert created.json()["email"] == "mixedcase@example.com"
    assert "password_hash" not in created.json()
    user = api.db.get(User, created.json()["id"])
    assert not user.is_active and user.status == "pending_verification"
    assert api.db.get(Profile, user.id).display_name == "New Student"
    assert api.db.query(AuditEvent).filter_by(event="user.registered").count() == 1
    assert _register(api.client, email="mixedcase@example.com").status_code == 409
    assert api.db.query(User).count() == 1
    assert api.db.query(EmailOutbox).count() == 1


@pytest.mark.parametrize("status", ["active", "suspended", "disabled", "pending_verification"])
def test_login_rejects_wrong_password_and_inactive_accounts(api, status):
    user, _, _ = api.account()
    user.status = status
    user.is_active = status == "active"
    api.db.commit()
    response = api.client.post("/api/v1/auth/login", headers={"Origin": api.settings.frontend_origin}, json={
        "email": user.email, "password": "wrong" if status == "active" else "correct horse battery",
    })
    assert response.status_code == 401
    unknown = api.client.post("/api/v1/auth/login", headers={"Origin": api.settings.frontend_origin}, json={"email": "unknown@example.com", "password": "wrong"})
    assert unknown.status_code == 401
    assert response.json() == unknown.json()
    assert api.db.query(AuditEvent).filter_by(event="auth.login", outcome="failure").count() == 2


@pytest.mark.parametrize("state", ["invalid", "expired"])
def test_verification_rejects_invalid_and_expired_tokens(api, state):
    created = _register(api.client).json()
    token = api.queued_token("verify_email", created["id"])
    if state == "expired":
        entry = api.db.query(EmailToken).one()
        entry.expires_at = utcnow() - timedelta(seconds=1)
        api.db.commit()
    else:
        token = "x" * 43
    assert api.client.post("/api/v1/auth/verify-email", json={"token": token}).status_code == 400
    api.db.expire_all()
    assert not api.db.get(User, created["id"]).is_active


def test_resend_verification_invalidates_old_token_and_hides_unknown_accounts(api):
    user_id = _register(api.client).json()["id"]
    old = api.queued_token("verify_email", user_id)
    resent = api.client.post("/api/v1/auth/resend-verification", json={"email": "new@example.com"})
    unknown = api.client.post("/api/v1/auth/resend-verification", json={"email": "unknown@example.com"})
    assert resent.status_code == unknown.status_code == 202
    assert resent.json() == unknown.json()
    new = api.queued_token("verify_email", user_id)
    assert new != old
    assert api.client.post("/api/v1/auth/verify-email", json={"token": old}).status_code == 400
    assert api.client.post("/api/v1/auth/verify-email", json={"token": new}).status_code == 200
    assert api.db.query(EmailOutbox).count() == 2


@pytest.mark.parametrize("request_path,confirm_path", [
    ("forgot-password", "reset-password"),
    ("password-recovery/request", "password-recovery/confirm"),
])
def test_password_recovery_changes_password_revokes_sessions_and_is_single_use(api, request_path, confirm_path):
    user, tokens, headers = api.account()
    response = api.client.post(f"/api/v1/auth/{request_path}", json={"email": user.email})
    assert response.status_code == 202
    token = api.queued_token("password_reset", user.id)
    body = {"token": token, "new_password": "a new secure password 9"}
    assert api.client.post(f"/api/v1/auth/{confirm_path}", json=body).status_code == 200
    assert api.client.post(f"/api/v1/auth/{confirm_path}", json=body).status_code == 400
    assert api.client.get("/api/v1/auth/me", headers=headers).status_code == 401
    api.client.cookies.set("aprovaai_refresh", tokens.refresh_token)
    assert api.client.post("/api/v1/auth/refresh", headers={"Origin": api.settings.frontend_origin}).status_code == 401
    for password, status in [("correct horse battery", 401), (body["new_password"], 200)]:
        assert api.client.post("/api/v1/auth/login", headers={"Origin": api.settings.frontend_origin}, json={"email": user.email, "password": password}).status_code == status


def test_password_recovery_hides_unknown_and_inactive_accounts(api):
    user, _, _ = api.account()
    user.status = "suspended"
    user.is_active = False
    api.db.commit()
    known = api.client.post("/api/v1/auth/forgot-password", json={"email": user.email})
    unknown = api.client.post("/api/v1/auth/forgot-password", json={"email": "unknown@example.com"})
    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    assert api.db.query(PasswordReset).count() == api.db.query(EmailOutbox).count() == 0


@pytest.mark.parametrize("state", ["invalid", "expired", "superseded"])
def test_password_reset_rejects_unusable_tokens(api, state):
    user, _, headers = api.account()
    api.client.post("/api/v1/auth/forgot-password", json={"email": user.email})
    token = api.queued_token("password_reset", user.id)
    if state == "expired":
        api.db.query(PasswordReset).one().expires_at = utcnow() - timedelta(seconds=1)
        api.db.commit()
    elif state == "superseded":
        assert api.client.post("/api/v1/auth/forgot-password", json={"email": user.email}).status_code == 202
    else:
        token = "x" * 43
    assert api.client.post("/api/v1/auth/reset-password", json={
        "token": token, "new_password": "a new secure password 9",
    }).status_code == 400
    assert api.client.get("/api/v1/auth/me", headers=headers).status_code == 200


@pytest.mark.parametrize("password", ["short1", "onlyletterslong", "123456789012"])
def test_reset_rejects_weak_password_without_consuming_token(api, password):
    user, _, _ = api.account()
    api.client.post("/api/v1/auth/forgot-password", json={"email": user.email})
    token = api.queued_token("password_reset", user.id)
    assert api.client.post("/api/v1/auth/reset-password", json={"token": token, "new_password": password}).status_code == 422
    api.db.expire_all()
    assert api.db.query(PasswordReset).one().used_at is None


@pytest.mark.parametrize("mode", ["bearer", "cookie"])
def test_logout_revokes_session_and_clears_cookies(api, mode):
    user, tokens, headers = api.account()
    api.client.cookies.set("aprovaai_refresh", tokens.refresh_token)
    response = api.client.post("/api/v1/auth/logout", headers=(
        headers if mode == "bearer" else {"Origin": api.settings.frontend_origin}
    ))
    assert response.status_code == 200
    assert 'aprovaai_refresh=""' in response.headers.get("set-cookie", "")
    assert 'aprovaai_admin_docs=""' in response.headers.get("set-cookie", "")
    assert api.client.get("/api/v1/auth/me", headers=headers).status_code == 401
    api.db.expire_all()
    assert api.db.get(AuthSession, tokens.session_id).revoked_at is not None
    assert api.db.query(RefreshToken).filter_by(session_id=tokens.session_id).one().revoked_at is not None
    assert api.db.query(AuditEvent).filter_by(event="auth.logout", outcome="success").count() == 1


def test_session_listing_and_revocation_are_restricted_to_owner(api):
    user, first, headers = api.account()
    other, other_tokens, other_headers = api.account()
    second = SessionService().create(api.db, user, api.settings)
    api.db.commit()
    listing = api.client.get("/api/v1/auth/sessions", headers=headers)
    assert listing.status_code == 200
    assert {item["id"] for item in listing.json()} == {first.session_id, second.session_id}
    assert all("token_hash" not in item for item in listing.json())
    for session_id in [other_tokens.session_id, "missing"]:
        assert api.client.delete(f"/api/v1/auth/sessions/{session_id}", headers=headers).status_code == 404
    assert api.client.delete(f"/api/v1/auth/sessions/{second.session_id}", headers=headers).status_code == 200
    assert api.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {second.access_token}"}).status_code == 401
    assert api.client.get("/api/v1/auth/me", headers=headers).status_code == 200
    assert api.client.get("/api/v1/auth/me", headers=other_headers).status_code == 200


def test_logout_all_revokes_only_current_users_sessions(api):
    user, first, headers = api.account()
    _, _, other_headers = api.account()
    second = SessionService().create(api.db, user, api.settings)
    api.db.commit()
    response = api.client.post("/api/v1/auth/logout-all", headers=headers)
    assert response.status_code == 200
    for tokens in [first, second]:
        assert api.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens.access_token}"}).status_code == 401
        api.client.cookies.set("aprovaai_refresh", tokens.refresh_token)
        assert api.client.post("/api/v1/auth/refresh", headers={"Origin": api.settings.frontend_origin}).status_code == 401
    assert api.client.get("/api/v1/auth/me", headers=other_headers).status_code == 200


@pytest.mark.parametrize("path", ["refresh", "logout"])
@pytest.mark.parametrize("origin", [None, "https://untrusted.example"])
def test_cookie_auth_rejects_missing_or_untrusted_origin(api, path, origin):
    _, tokens, headers = api.account()
    api.client.cookies.set("aprovaai_refresh", tokens.refresh_token)
    response = api.client.post(f"/api/v1/auth/{path}", headers={} if origin is None else {"Origin": origin})
    assert response.status_code == 403
    assert api.client.get("/api/v1/auth/me", headers=headers).status_code == 200


@pytest.mark.parametrize("path", ["refresh", "logout"])
@pytest.mark.parametrize("cookie", [None, "invalid-token"])
def test_cookie_auth_rejects_missing_or_invalid_refresh(api, path, cookie):
    if cookie:
        api.client.cookies.set("aprovaai_refresh", cookie)
    assert api.client.post(f"/api/v1/auth/{path}", headers={"Origin": api.settings.frontend_origin}).status_code == 401


def test_refresh_reuse_revokes_family_through_http(api):
    _, tokens, headers = api.account()
    api.client.cookies.set("aprovaai_refresh", tokens.refresh_token)
    origin = {"Origin": api.settings.frontend_origin}
    refreshed = api.client.post("/api/v1/auth/refresh", headers=origin)
    assert refreshed.status_code == 200
    successor = refreshed.cookies.get("aprovaai_refresh")
    api.client.cookies.clear()
    api.client.cookies.set("aprovaai_refresh", tokens.refresh_token)
    assert api.client.post("/api/v1/auth/refresh", headers=origin).status_code == 401
    api.client.cookies.set("aprovaai_refresh", successor)
    assert api.client.post("/api/v1/auth/refresh", headers=origin).status_code == 401
    assert api.client.get("/api/v1/auth/me", headers=headers).status_code == 401
    assert api.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {refreshed.json()['access_token']}"}).status_code == 401


@pytest.mark.parametrize("target", ["session", "refresh"])
def test_expired_sessions_and_refresh_tokens_are_rejected(api, target):
    _, tokens, headers = api.account()
    entry = (api.db.get(AuthSession, tokens.session_id) if target == "session" else
             api.db.query(RefreshToken).filter_by(session_id=tokens.session_id).one())
    entry.expires_at = utcnow() - timedelta(seconds=1)
    api.db.commit()
    api.client.cookies.set("aprovaai_refresh", tokens.refresh_token)
    assert api.client.post("/api/v1/auth/refresh", headers={"Origin": api.settings.frontend_origin}).status_code == 401
    if target == "session":
        assert api.client.get("/api/v1/auth/me", headers=headers).status_code == 401


@pytest.mark.parametrize("change", ["expired", "issuer", "purpose", "kid", "missing_sid", "version", "unknown_session", "malformed", "algorithm"])
def test_api_rejects_invalid_access_tokens(api, change):
    _, tokens, _ = api.account()
    payload = jwt.decode(tokens.access_token, options={"verify_signature": False})
    kid = api.settings.jwt_kid
    if change == "expired":
        payload["exp"] = 1
    elif change == "issuer":
        payload["iss"] = "another-issuer"
    elif change == "purpose":
        payload["typ"] = "admin_docs"
    elif change == "kid":
        kid = "unknown-key"
    elif change == "missing_sid":
        del payload["sid"]
    elif change == "version":
        payload["ver"] += 1
    elif change == "unknown_session":
        payload["sid"] = "missing"
    token = jwt.encode(payload, api.settings.jwt_private_key, algorithm="EdDSA", headers={"kid": kid})
    if change == "malformed":
        token = "not-a-jwt"
    elif change == "algorithm":
        token = jwt.encode(payload, "test-secret" * 4, algorithm="HS256", headers={"kid": kid})
    assert api.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


@pytest.mark.parametrize("role,expected", [("student", 403), ("teacher", 200), ("admin", 403)])
def test_teacher_route_role_matrix(api, role, expected):
    user, _, headers = api.account(role)
    response = api.client.get("/api/v1/auth/test/teacher", headers=headers)
    assert response.status_code == expected
    if expected == 200:
        assert response.json()["teacher_id"] == user.id


@pytest.mark.parametrize("status", ["suspended", "disabled"])
def test_admin_status_change_revokes_sessions_and_blocks_login(api, status):
    _, _, admin_headers = api.account("admin")
    user, tokens, headers = api.account()
    response = api.client.patch(f"/api/v1/admin/users/{user.id}/status", headers=admin_headers, json={"status": status})
    assert response.status_code == 200
    api.db.expire_all()
    assert api.db.get(User, user.id).status == status
    assert not api.db.get(User, user.id).is_active
    assert api.client.get("/api/v1/auth/me", headers=headers).status_code == 401
    assert api.client.post("/api/v1/auth/login", headers={"Origin": api.settings.frontend_origin}, json={"email": user.email, "password": "correct horse battery"}).status_code == 401
    api.client.cookies.set("aprovaai_refresh", tokens.refresh_token)
    assert api.client.post("/api/v1/auth/refresh", headers={"Origin": api.settings.frontend_origin}).status_code == 401
    event = api.db.query(AuditEvent).filter_by(event="user.status.changed").one()
    assert event.subject_id == user.id and event.details == {"status": status}
    assert api.client.patch(f"/api/v1/admin/users/{user.id}/status", headers=admin_headers, json={"status": "active"}).status_code == 200
    assert api.client.post("/api/v1/auth/login", headers={"Origin": api.settings.frontend_origin}, json={"email": user.email, "password": "correct horse battery"}).status_code == 200


@pytest.mark.parametrize("role", ["student", "teacher"])
@pytest.mark.parametrize("field,value", [("role", "admin"), ("status", "disabled")])
def test_non_admin_cannot_manage_users(api, role, field, value):
    _, _, headers = api.account(role)
    target, _, _ = api.account()
    assert api.client.patch(f"/api/v1/admin/users/{target.id}/{field}", headers=headers, json={field: value}).status_code == 403


@pytest.mark.parametrize("field", ["role", "status"])
def test_admin_updates_validate_values_and_missing_users(api, field):
    _, _, headers = api.account("admin")
    value = "student" if field == "role" else "disabled"
    assert api.client.patch(f"/api/v1/admin/users/missing/{field}", headers=headers, json={field: value}).status_code == 404
    assert api.client.patch(f"/api/v1/admin/users/missing/{field}", headers=headers, json={field: "invalid"}).status_code == 422


def test_admin_cannot_activate_unverified_account(api):
    _, _, headers = api.account("admin")
    user_id = _register(api.client).json()["id"]
    assert api.client.patch(f"/api/v1/admin/users/{user_id}/status", headers=headers, json={"status": "active"}).status_code == 409


@pytest.mark.parametrize("scope", ["ip", "identity"])
def test_login_rate_limit_returns_429_and_retry_after(api, scope):
    # Variar o IP isola o limite por identidade; variar o e-mail isola o limite por IP.
    for index in range(11):
        address = f"192.0.2.{index + 1}" if scope == "identity" else "192.0.2.1"
        email = "unknown@example.com" if scope == "identity" else f"unknown{index}@example.com"
        with TestClient(api.client.app, client=(address, 50000)) as client:
            response = client.post("/api/v1/auth/login", headers={"Origin": api.settings.frontend_origin}, json={"email": email, "password": "wrong"})
        assert response.status_code == (401 if index < 10 else 429)
    assert response.headers["retry-after"] == "900"


def test_rate_limit_window_resets_without_sleeping(api):
    limiter = RateLimitService()
    key = "test:identity:user@example.com"
    assert limiter.consume(api.db, key, 1, 60)
    assert not limiter.consume(api.db, key, 1, 60)
    api.db.query(RateLimitBucket).one().window_started_at = utcnow() - timedelta(seconds=61)
    api.db.flush()
    assert limiter.consume(api.db, key, 1, 60)


def test_profile_read_update_and_user_isolation(api):
    user, _, headers = api.account()
    other, _, other_headers = api.account()
    assert api.client.get("/api/v1/profiles/me", headers=headers).json()["user_id"] == user.id
    updated = api.client.patch("/api/v1/profiles/me", headers=headers, json={"display_name": "Updated Name", "preferences": {"theme": "dark"}})
    assert updated.status_code == 200
    assert updated.json()["display_name"] == "Updated Name"
    assert updated.json()["preferences"] == {"theme": "dark"}
    assert api.client.get("/api/v1/profiles/me", headers=other_headers).json()["display_name"] == "Test User"
    assert api.client.patch("/api/v1/profiles/me", headers=headers, json={"preferences": {str(i): i for i in range(31)}}).status_code == 400
    assert api.client.patch("/api/v1/profiles/me", headers=headers, json={"display_name": "x"}).status_code == 422
    api.db.delete(api.db.get(Profile, other.id))
    api.db.commit()
    assert api.client.get("/api/v1/profiles/me", headers=other_headers).status_code == 404


@pytest.mark.parametrize("filename,content,mime", [
    ("proof.pdf", b"%PDF-1.7\nexample", "application/pdf"),
    ("proof.png", b"\x89PNG\r\n\x1a\nexample", "image/png"),
    ("proof.jpeg", b"\xff\xd8\xffexample", "image/jpeg"),
])
def test_document_upload_and_download_permissions(api, filename, content, mime):
    _, _, owner = api.account()
    _, _, stranger = api.account()
    _, _, admin = api.account("admin")
    uploaded = _upload(api, owner, filename, content)
    assert uploaded.status_code == 201
    assert uploaded.json()["content_type"] == mime
    assert uploaded.json()["size_bytes"] == len(content)
    assert "storage_name" not in uploaded.json()
    path = f"/api/v1/media/documents/{uploaded.json()['id']}"
    for headers in [owner, admin]:
        downloaded = api.client.get(path, headers=headers)
        assert downloaded.status_code == 200 and downloaded.content == content
        assert downloaded.headers["cache-control"] == "no-store"
        assert downloaded.headers["x-content-type-options"] == "nosniff"
        assert "attachment" in downloaded.headers["content-disposition"]
    assert api.client.get(path, headers=stranger).status_code == 403
    assert api.client.get("/api/v1/media/documents/missing", headers=owner).status_code == 404
    media = api.db.get(MediaItem, uploaded.json()["id"])
    (api.settings.media_root / media.storage_name).unlink()
    assert api.client.get(path, headers=owner).status_code == 404


@pytest.mark.parametrize("filename,content,status", [
    ("proof.pdf", b"", 400), ("proof.pdf", b"not a PDF", 400),
    ("proof.exe", b"%PDF-1.7", 400), ("proof.png", b"%PDF-1.7", 400),
    ("proof.pdf", b"%PDF-" + b"x" * 1024, 413),
])
def test_invalid_uploads_leave_no_files_or_database_records(api, filename, content, status):
    _, _, headers = api.account()
    assert _upload(api, headers, filename, content).status_code == status
    assert api.db.query(MediaItem).count() == 0
    assert list(api.settings.media_root.iterdir()) == []


@pytest.mark.parametrize("role", ["teacher", "admin"])
def test_upload_is_restricted_to_students(api, role):
    _, _, headers = api.account(role)
    assert _upload(api, headers).status_code == 403


def test_upload_sanitizes_filename(api):
    _, _, headers = api.account()
    response = _upload(api, headers, "../../proof.pdf")
    assert response.status_code == 201
    assert response.json()["original_name"] == "proof.pdf"
    assert len(list(api.settings.media_root.iterdir())) == 1


def test_teacher_application_creates_notification_and_cannot_be_duplicated(api):
    user, _, headers = api.account()
    _, _, other_headers = api.account()
    assert api.client.get("/api/v1/teacher-applications/me", headers=headers).status_code == 404
    document = _upload(api, headers).json()["id"]
    response = api.client.post("/api/v1/teacher-applications", headers=headers, json=_application([document]))
    assert response.status_code == 201
    assert response.json()["status"] == "pending"
    assert response.json()["document_ids"] == [document]
    assert response.json()["user_id"] == user.id
    assert api.client.get("/api/v1/teacher-applications/me", headers=headers).json() == response.json()
    assert api.client.get("/api/v1/teacher-applications/me", headers=other_headers).status_code == 404
    assert api.client.post("/api/v1/teacher-applications", headers=headers, json=_application([document])).status_code == 409
    notifications = api.client.get("/api/v1/notifications/me", headers=headers)
    assert notifications.status_code == 200 and len(notifications.json()) == 1
    notification = notifications.json()[0]
    assert notification["details"]["application_id"] == response.json()["id"]
    path = f"/api/v1/notifications/{notification['id']}/read"
    assert api.client.get("/api/v1/notifications/me", headers=other_headers).json() == []
    assert api.client.patch(path, headers=other_headers).status_code == 404
    read = api.client.patch(path, headers=headers)
    assert read.status_code == 200 and read.json()["read_at"] is not None
    assert api.client.patch(path, headers=headers).json()["read_at"] == read.json()["read_at"]
    assert api.client.patch("/api/v1/notifications/missing/read", headers=headers).status_code == 404


@pytest.mark.parametrize("case,status", [("missing", 400), ("foreign", 403), ("duplicate", 422), ("empty", 422)])
def test_teacher_application_rejects_invalid_documents(api, case, status):
    _, _, headers = api.account()
    _, _, other_headers = api.account()
    if case == "missing":
        documents = ["missing"]
    elif case == "empty":
        documents = []
    else:
        document = _upload(api, other_headers if case == "foreign" else headers).json()["id"]
        documents = [document] * (2 if case == "duplicate" else 1)
    assert api.client.post("/api/v1/teacher-applications", headers=headers, json=_application(documents)).status_code == status
    assert api.db.query(Notification).count() == 0


@pytest.mark.parametrize("role", ["teacher", "admin"])
def test_teacher_application_requires_student_role(api, role):
    _, _, headers = api.account(role)
    assert api.client.post("/api/v1/teacher-applications", headers=headers, json=_application(["missing"])).status_code == 403


@pytest.mark.parametrize("path", ["register", "forgot-password"])
def test_email_unavailability_returns_503_without_partial_registration(api, path):
    app = FastAPI()
    app.include_router(api.create_router(api.get_db, api.settings))
    with TestClient(app) as client:
        response = (_register(client) if path == "register" else
                    client.post("/api/v1/auth/forgot-password", json={"email": "unknown@example.com"}))
    assert response.status_code == 503
    assert api.db.query(User).count() == api.db.query(EmailOutbox).count() == 0


@pytest.mark.parametrize("purpose", ["verify_email", "password_reset"])
def test_outbox_encrypts_delivers_and_erases_token(api, purpose):
    user, _, _ = api.account()
    service = EmailOutboxService(api.settings)
    sender = CapturingEmailSender()
    raw = "secret-token-for-testing"
    service.enqueue(api.db, user.id, user.email, purpose, raw)
    api.db.commit()
    message = api.db.query(EmailOutbox).one()
    assert raw not in message.encrypted_token
    assert service.deliver_one(api.db, sender)
    assert len(sender.messages) == 1
    assert sender.messages[0][0] == user.email and raw in sender.messages[0][2]
    assert message.status == "delivered" and message.delivered_at is not None
    assert message.encrypted_token == ""
    assert not service.deliver_one(api.db, sender)


def test_outbox_retries_without_leaking_secrets_and_stops_after_limit(api):
    user, _, _ = api.account()
    service = EmailOutboxService(api.settings)
    service.enqueue(api.db, user.id, user.email, "verify_email", "secret-token")
    api.db.commit()

    class FailingSender:
        def send(self, *args):
            raise RuntimeError("secret-token should never appear in persisted errors")

    for attempt in range(1, 9):
        message = api.db.query(EmailOutbox).one()
        message.next_attempt_at = utcnow() - timedelta(seconds=1)
        api.db.commit()
        assert service.deliver_one(api.db, FailingSender())
        assert message.attempts == attempt
        assert "secret-token" not in message.last_error
        assert message.status == ("failed" if attempt == 8 else "pending")
        if attempt < 8:
            assert message.next_attempt_at > utcnow()
            assert not service.deliver_one(api.db, FailingSender())
    assert not service.deliver_one(api.db, FailingSender())


@pytest.mark.parametrize("path,limit,body", [
    ("resend-verification", 3, {"email": "unknown@example.com"}),
    ("forgot-password", 3, {"email": "unknown@example.com"}),
    ("verify-email", 10, {"token": "x" * 43}),
])
def test_public_auth_routes_enforce_rate_limits(api, path, limit, body):
    for _ in range(limit):
        response = api.client.post(f"/api/v1/auth/{path}", json=body)
        assert response.status_code in {202, 400}
    blocked = api.client.post(f"/api/v1/auth/{path}", json=body)
    assert blocked.status_code == 429
    assert blocked.headers["retry-after"] == "3600"


def test_registration_rate_limit_prevents_additional_accounts(api):
    for index in range(5):
        assert _register(api.client, email=f"new{index}@example.com").status_code == 201
    assert _register(api.client, email="overflow@example.com").status_code == 429
    assert api.db.query(User).count() == 5


def test_refresh_rate_limit(api):
    origin = {"Origin": api.settings.frontend_origin}
    for _ in range(30):
        assert api.client.post("/api/v1/auth/refresh", headers=origin).status_code == 401
    blocked = api.client.post("/api/v1/auth/refresh", headers=origin)
    assert blocked.status_code == 429 and blocked.headers["retry-after"] == "60"


@pytest.mark.parametrize("state", ["suspended", "disabled", "version_changed", "foreign_session"])
def test_valid_signature_does_not_bypass_current_account_or_session_state(api, state):
    user, tokens, headers = api.account()
    if state in {"suspended", "disabled"}:
        user.status = state
        user.is_active = False
    elif state == "version_changed":
        user.token_version += 1
    else:
        other, _, _ = api.account()
        api.db.get(AuthSession, tokens.session_id).user_id = other.id
    api.db.commit()
    assert api.client.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_token_role_claim_cannot_grant_administrative_permissions(api):
    user, tokens, _ = api.account()
    payload = jwt.decode(tokens.access_token, options={"verify_signature": False})
    payload["role"] = "ADMIN"
    token = jwt.encode(payload, api.settings.jwt_private_key, algorithm="EdDSA", headers={"kid": api.settings.jwt_kid})
    headers = {"Authorization": f"Bearer {token}"}
    assert api.client.patch(f"/api/v1/admin/users/{user.id}/role", headers=headers, json={"role": "admin"}).status_code == 403
    assert api.client.get("/api/v1/auth/me", headers=headers).json()["role"] == "student"


def test_setting_same_role_preserves_session(api):
    _, _, admin = api.account("admin")
    user, _, headers = api.account()
    assert api.client.patch(f"/api/v1/admin/users/{user.id}/role", headers=admin, json={"role": "student"}).status_code == 200
    assert api.client.get("/api/v1/auth/me", headers=headers).status_code == 200


def test_profile_validation_does_not_persist_partial_updates(api):
    user, _, headers = api.account()
    assert api.client.patch("/api/v1/profiles/me", headers=headers, json={
        "display_name": "Should Roll Back", "preferences": {str(i): i for i in range(31)},
    }).status_code == 400
    api.db.expire_all()
    assert api.db.get(Profile, user.id).display_name == "Test User"


def test_upload_commit_failure_removes_file_and_rolls_back_metadata(api, monkeypatch):
    _, _, headers = api.account()

    def fail_commit(self):
        raise RuntimeError("Simulated database failure")

    monkeypatch.setattr(Session, "commit", fail_commit)
    with TestClient(api.client.app, raise_server_exceptions=False) as client:
        response = client.post("/api/v1/media/documents", headers=headers,
                               files={"file": ("proof.pdf", b"%PDF-1.7", "application/pdf")})
    assert response.status_code == 500
    api.db.expire_all()
    assert api.db.query(MediaItem).count() == 0
    assert list(api.settings.media_root.iterdir()) == []


@pytest.fixture
def full_app_client(api, monkeypatch):
    # Usa a aplicação real para validar middleware, cookies e documentação.
    with monkeypatch.context() as startup_patch:
        startup_patch.setattr(Settings, "from_env", classmethod(lambda cls: api.settings))
        main = importlib.reload(importlib.import_module("app.main"))
    main.app.dependency_overrides[main.get_db] = api.get_db
    with TestClient(main.app, follow_redirects=False) as client:
        yield client
    main.app.dependency_overrides.clear()


@pytest.mark.parametrize("case,status", [("wrong_password", 401), ("unknown", 401), ("student", 403)])
def test_admin_docs_login_rejects_invalid_credentials_and_non_admin(api, full_app_client, case, status):
    user, _, _ = api.account("student" if case == "student" else "admin")
    response = full_app_client.post("/admin/login", headers={"Origin": "http://testserver"}, data={
        "email": "unknown@example.com" if case == "unknown" else user.email,
        "password": "wrong" if case == "wrong_password" else "correct horse battery",
    })
    assert response.status_code == status
    assert "aprovaai_admin_docs" not in response.cookies
    assert api.db.query(AuditEvent).filter_by(event="admin_docs.login", outcome="failure").count() == 1


@pytest.mark.parametrize("origin", [None, "null", "https://untrusted.example"])
def test_admin_docs_login_requires_allowed_origin(api, full_app_client, origin):
    user, _, _ = api.account("admin")
    response = full_app_client.post("/admin/login", headers={} if origin is None else {"Origin": origin},
                                    data={"email": user.email, "password": "correct horse battery"})
    assert response.status_code == 403


@pytest.mark.parametrize("token_type", ["invalid", "access", "expired_docs", "revoked_docs"])
def test_docs_rejects_invalid_purpose_expired_or_revoked_tokens(api, full_app_client, token_type):
    user, tokens, _ = api.account("admin")
    service = SessionService()
    token = service.create_admin_docs_token(user, tokens.session_id, api.settings)
    if token_type == "invalid":
        token = "invalid"
    elif token_type == "access":
        token = tokens.access_token
    elif token_type == "expired_docs":
        token = service.create_admin_docs_token(user, tokens.session_id, replace(api.settings, access_token_minutes=-1))
    else:
        service.revoke_session(api.db, tokens.session_id)
        api.db.commit()
    full_app_client.cookies.set("aprovaai_admin_docs", token)
    assert full_app_client.get("/docs").status_code == 303
    assert full_app_client.get("/openapi.json").status_code == 403


def test_admin_docs_login_rate_limit(api, full_app_client):
    for _ in range(5):
        assert full_app_client.post("/admin/login", headers={"Origin": "http://testserver"},
                                    data={"email": "unknown@example.com", "password": "wrong"}).status_code == 401
    blocked = full_app_client.post("/admin/login", headers={"Origin": "http://testserver"},
                                    data={"email": "unknown@example.com", "password": "wrong"})
    assert blocked.status_code == 429 and blocked.headers["retry-after"] == "900"


def test_security_headers_and_cache_control_on_real_app(full_app_client):
    health = full_app_client.get("/api/health")
    assert health.status_code == 200 and health.json() == {"status": "ok"}
    for path in ["/admin/login", "/docs", "/openapi.json", "/api/v1/auth/me"]:
        response = full_app_client.get(path)
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"
        expected_policy = "same-origin" if path == "/admin/login" else "no-referrer"
        assert response.headers["referrer-policy"] == expected_policy
        assert response.headers["x-request-id"]


def test_secure_cookie_configuration(api):
    user, _, _ = api.account()
    settings = replace(api.settings, cookie_secure=True, cookie_samesite="strict")
    app = FastAPI()
    app.include_router(api.create_router(api.get_db, settings, CapturingEmailSender()))
    with TestClient(app, base_url="https://testserver") as client:
        login = client.post("/api/v1/auth/login", headers={"Origin": settings.frontend_origin}, json={"email": user.email, "password": "correct horse battery"})
        assert login.status_code == 200
        cookie = login.headers["set-cookie"]
        for attribute in ["Secure", "HttpOnly", "SameSite=strict", "Path=/api/v1/auth"]:
            assert attribute in cookie
        assert client.post("/api/v1/auth/refresh", headers={"Origin": settings.frontend_origin}).status_code == 200


# Integration transport: cookie-authenticated native requests and writes.
@pytest.mark.parametrize("origin", [None, "null", "https://untrusted.example", "http://testserver"])
def test_web_login_requires_configured_origin(api, origin):
    user, _, _ = api.account()
    response = api.client.post("/api/v1/auth/login", json={"email": user.email, "password": "correct horse battery"},
                               headers={} if origin is None else {"Origin": origin})
    assert response.status_code == 403
    assert "set-cookie" not in response.headers


def test_access_cookie_login_refresh_and_logout(api):
    user, _, _ = api.account()
    origin = {"Origin": api.settings.frontend_origin}
    login = api.client.post("/api/v1/auth/login", headers=origin,
                            json={"email": user.email, "password": "correct horse battery"})
    token = login.json()["access_token"]
    header = next(h for h in login.headers.get_list("set-cookie") if h.startswith("aprovaai_access="))
    assert "HttpOnly" in header and "Path=/api;" in header and "Max-Age=900" in header
    assert "Domain=" not in header
    assert api.client.get("/api/v1/auth/me").json()["id"] == user.id
    refreshed = api.client.post("/api/v1/auth/refresh", headers=origin)
    assert api.client.cookies.get("aprovaai_access") == refreshed.json()["access_token"] != token
    assert api.client.post("/api/v1/auth/logout", headers=origin).status_code == 200
    assert api.client.cookies.get("aprovaai_access") is None
    assert api.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


@pytest.mark.parametrize("authorization", ["Bearer invalid", "Basic invalid", "Bearer", ""])
def test_explicit_bad_authorization_never_uses_cookie(api, authorization):
    _, tokens, _ = api.account()
    api.client.cookies.set("aprovaai_access", tokens.access_token, path="/api")
    assert api.client.get("/api/v1/auth/me", headers={"Authorization": authorization}).status_code == 401


def test_valid_bearer_selects_identity_even_with_different_cookie(api):
    first, tokens, _ = api.account()
    second, _, headers = api.account()
    api.client.cookies.set("aprovaai_access", tokens.access_token, path="/api")
    assert api.client.get("/api/v1/auth/me").json()["id"] == first.id
    assert api.client.get("/api/v1/auth/me", headers=headers).json()["id"] == second.id


@pytest.mark.parametrize("origin", [None, "null", "https://untrusted.example"])
def test_profile_cookie_write_requires_origin(api, origin):
    _, tokens, _ = api.account()
    api.client.cookies.set("aprovaai_access", tokens.access_token, path="/api")
    response = api.client.patch("/api/v1/profiles/me", json={"display_name": "Changed"},
                               headers={} if origin is None else {"Origin": origin})
    assert response.status_code == 403
    assert api.client.get("/api/v1/profiles/me").json()["display_name"] == "Test User"


def test_cookie_write_and_global_logout(api):
    _, tokens, _ = api.account()
    api.client.cookies.set("aprovaai_access", tokens.access_token, domain="testserver.local", path="/api")
    origin = {"Origin": api.settings.frontend_origin}
    assert api.client.patch("/api/v1/profiles/me", json={"display_name": "Changed"}, headers=origin).status_code == 200
    assert api.client.post("/api/v1/auth/logout-all", headers=origin).status_code == 200
    assert api.client.cookies.get("aprovaai_access") is None
    assert api.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens.access_token}"}).status_code == 401


def test_invalid_web_logout_clears_stale_cookies(api):
    api.client.cookies.set("aprovaai_access", "invalid", domain="testserver.local", path="/api")
    api.client.cookies.set("aprovaai_refresh", "invalid", domain="testserver.local", path="/api/v1/auth")
    response = api.client.post("/api/v1/auth/logout", headers={"Origin": api.settings.frontend_origin})
    assert response.status_code == 401
    assert api.client.cookies.get("aprovaai_access") is None
    assert api.client.cookies.get("aprovaai_refresh") is None


def test_admin_moderation_audit_is_owned_and_idempotent(api, monkeypatch):
    monkeypatch.setenv('INTERNAL_SERVICE_TOKEN','shared-internal-test-secret')
    admin, _, admin_headers = api.account("admin")
    _, _, student_headers = api.account("student")
    body={"operation_id":str(uuid4()),"item_type":"lesson","item_id":str(uuid4()),
          "decision":"hide","justification":"Decisão revisada"}
    url="/api/v1/admin/audit/moderation"
    assert api.client.post(url,json=body,headers=student_headers).status_code==403
    assert api.client.post(url,json=body).status_code==401
    assert api.client.post(url,json=body,headers=admin_headers).status_code==403
    admin_headers={**admin_headers,'X-Service-Token':'shared-internal-test-secret'}
    first=api.client.post(url,json=body,headers=admin_headers)
    second=api.client.post(url,json=body,headers=admin_headers)
    assert first.status_code==second.status_code==201
    assert first.json()['audit_id']==second.json()['audit_id']
    assert api.client.post(url,json={**body,"decision":"delete"},headers=admin_headers).status_code==409
    records=api.db.query(AuditEvent).filter_by(event="content.moderated").all()
    assert len(records)==1 and records[0].actor_id==admin.id
