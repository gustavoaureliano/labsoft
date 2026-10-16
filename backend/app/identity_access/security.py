from __future__ import annotations

import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerifyMismatchError,
    VerificationError,
)


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