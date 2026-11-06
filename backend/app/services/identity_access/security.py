from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerifyMismatchError,
    VerificationError,
)
from jwt import InvalidTokenError

from .config import Settings
from .models import User


_passwords = PasswordHasher()


def hash_password(password: str) -> str:
    return _passwords.hash(password)


def verify_password(
    password_hash: str,
    password: str,
) -> bool:
    try:
        return _passwords.verify(
            password_hash, password
        )
    except (
        InvalidHashError,
        VerifyMismatchError,
        VerificationError,
    ):
        return False


def generate_secret() -> str:
    return secrets.token_urlsafe(32)


def token_digest(secret: str) -> str:
    return hashlib.sha256(
        secret.encode("utf-8")
    ).hexdigest()


def create_access_token(
    user: User,
    session_id: str,
    settings: Settings,
    purpose: str = "access",
) -> tuple[str, datetime]:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(
        minutes=settings.access_token_minutes
    )
    roles = {
        "student": "ALUNO",
        "teacher": "PROFESSOR",
        "admin": "ADMIN",
    }
    token = jwt.encode(
        {
            "sub": user.id,
            "role": roles[user.role],
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "typ": purpose,
            "sid": session_id,
            "jti": str(uuid4()),
            "iat": now,
            "nbf": now,
            "exp": expires_at,
            "ver": user.token_version,
        },
        settings.jwt_private_key,
        algorithm="EdDSA",
        headers={"kid": settings.jwt_kid},
    )
    return token, expires_at.replace(tzinfo=None)


def decode_access_token(
    token: str,
    settings: Settings,
    expected_purpose: str = "access",
) -> dict:
    header = jwt.get_unverified_header(token)
    if (
        header.get("alg") != "EdDSA"
        or header.get("kid") != settings.jwt_kid
    ):
        raise InvalidTokenError("Unsupported signing key.")

    payload = jwt.decode(
        token,
        settings.jwt_public_key,
        algorithms=["EdDSA"],
        audience=settings.jwt_audience,
        issuer=settings.jwt_issuer,
        options={
            "require": [
                "exp",
                "iat",
                "nbf",
                "sub",
                "jti",
                "sid",
                "iss",
                "aud",
                "typ",
                "ver",
            ],
        },
    )
    if payload.get("typ") != expected_purpose:
        raise InvalidTokenError("Unexpected token purpose.")
    if not all(
        isinstance(payload.get(field), str) and payload[field]
        for field in ("sub", "sid", "jti")
    ):
        raise InvalidTokenError("Invalid token claims.")
    return payload
