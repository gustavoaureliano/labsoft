from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerifyMismatchError,
    VerificationError,
)
from jwt import InvalidTokenError


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
    subject: str,
    signing_key: str,
    expires_at: datetime,
) -> str:
    return jwt.encode(
        {
            "sub": subject,
            "jti": generate_secret(),
            "iat": datetime.now(timezone.utc),
            "exp": expires_at,
        },
        signing_key,
        algorithm="HS256",
    )


def decode_access_token(
    token: str,
    signing_key: str,
) -> str:
    payload = jwt.decode(
        token,
        signing_key,
        algorithms=["HS256"],
        options={"require": ["exp", "iat", "sub", "jti"]},
    )
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise InvalidTokenError("Invalid token subject.")
    return subject
