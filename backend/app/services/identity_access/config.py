from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)


def _int_env(key: str, default: int) -> int:
    return int(os.environ.get(key, str(default)))


def _decode_key(key: str, env_name: str) -> bytes:
    try:
        return base64.urlsafe_b64decode(key + "=" * (-len(key) % 4))
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{env_name} must be valid base64.") from exc


@dataclass(frozen=True)
class Settings:
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    jwt_private_key: str = ""
    jwt_public_key: str = ""
    jwt_kid: str = ""
    jwt_issuer: str = "aprovaai-auth"
    jwt_audience: str = "aprovaai-api"
    email_encryption_key: str = ""
    verification_hours: int = 24
    reset_minutes: int = 20
    media_root: Path = Path("./private_uploads")
    max_document_bytes: int = 8 * 1024 * 1024
    password_reset_url: str = (
        "http://localhost:5173/redefinir-senha"
    )
    frontend_origin: str = "http://localhost:3000"
    public_app_url: str = "http://localhost:3000"
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    brevo_api_key: str | None = None
    brevo_sender_email: str | None = None
    brevo_sender_name: str = "AprovaAí"

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_starttls: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        private_key_raw = os.getenv("AA_JWT_PRIVATE_KEY_B64", "").strip()
        public_key_raw = os.getenv("AA_JWT_PUBLIC_KEY_B64", "").strip()
        if not private_key_raw:
            raise ValueError(
                "Configure AA_JWT_PRIVATE_KEY_B64 with an Ed25519 private key."
            )

        private_key_bytes = _decode_key(
            private_key_raw,
            "AA_JWT_PRIVATE_KEY_B64",
        )
        try:
            private_key = serialization.load_pem_private_key(
                private_key_bytes,
                password=None,
            )
        except (ValueError, TypeError) as exc:
            raise ValueError(
                "AA_JWT_PRIVATE_KEY_B64 must contain a valid PEM key."
            ) from exc
        if not isinstance(private_key, Ed25519PrivateKey):
            raise ValueError(
                "AA_JWT_PRIVATE_KEY_B64 must be an Ed25519 key."
            )

        derived_public_key = private_key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        if public_key_raw:
            configured_public_key = _decode_key(
                public_key_raw,
                "AA_JWT_PUBLIC_KEY_B64",
            )
            if configured_public_key != derived_public_key:
                raise ValueError(
                    "The configured Ed25519 public and private keys do not match."
                )
        else:
            configured_public_key = derived_public_key

        email_encryption_key = os.getenv(
            "AA_EMAIL_ENCRYPTION_KEY",
            "",
        ).strip()
        if email_encryption_key:
            try:
                Fernet(email_encryption_key.encode("ascii"))
            except (ValueError, TypeError) as exc:
                raise ValueError(
                    "AA_EMAIL_ENCRYPTION_KEY must be a valid Fernet key."
                ) from exc

        cookie_samesite = os.getenv(
            "AA_COOKIE_SAMESITE",
            "lax",
        ).lower()
        if cookie_samesite not in {"lax", "strict", "none"}:
            raise ValueError(
                "AA_COOKIE_SAMESITE must be lax, strict, or none."
            )
        if (
            cookie_samesite == "none"
            and os.getenv("AA_COOKIE_SECURE", "false").lower() != "true"
        ):
            raise ValueError(
                "AA_COOKIE_SECURE=true is required for SameSite=None."
            )

        return cls(
            access_token_minutes=_int_env(
                "AA_ACCESS_TOKEN_MINUTES",
                15,
            ),
            refresh_token_days=_int_env("AA_REFRESH_TOKEN_DAYS", 7),
            jwt_private_key=private_key_bytes.decode("utf-8"),
            jwt_public_key=configured_public_key.decode("utf-8"),
            jwt_kid=os.getenv("AA_JWT_KID", "ed25519-1"),
            jwt_issuer=os.getenv(
                "AA_JWT_ISSUER",
                "aprovaai-auth",
            ),
            jwt_audience=os.getenv(
                "AA_JWT_AUDIENCE",
                "aprovaai-api",
            ),
            email_encryption_key=email_encryption_key,
            verification_hours=_int_env(
                "AA_VERIFICATION_HOURS",
                24,
            ),
            reset_minutes=_int_env("AA_RESET_MINUTES", 20),
            media_root=Path(
                os.getenv("AA_MEDIA_ROOT", "./private_uploads")
            ),
            max_document_bytes=_int_env(
                "AA_MAX_DOCUMENT_BYTES", 8 * 1024 * 1024
            ),
            password_reset_url=os.getenv(
                "AA_PASSWORD_RESET_URL",
                "http://localhost:5173/redefinir-senha",
            ),
            frontend_origin=os.getenv(
                "AA_FRONTEND_ORIGIN",
                "http://localhost:3000",
            ),
            public_app_url=os.getenv(
                "AA_PUBLIC_APP_URL",
                "http://localhost:3000",
            ).rstrip("/"),
            cookie_secure=(
                os.getenv("AA_COOKIE_SECURE", "false").lower()
                == "true"
            ),
            cookie_samesite=cookie_samesite,
            brevo_api_key=os.getenv("BREVO_API_KEY"),
            brevo_sender_email=os.getenv("BREVO_SENDER_EMAIL"),
            brevo_sender_name=os.getenv(
                "BREVO_SENDER_NAME",
                "AprovaAí",
            ),
            smtp_host=os.getenv("AA_SMTP_HOST"),
            smtp_port=_int_env("AA_SMTP_PORT", 587),
            smtp_username=os.getenv("AA_SMTP_USERNAME"),
            smtp_password=os.getenv("AA_SMTP_PASSWORD"),
            smtp_from=os.getenv("AA_SMTP_FROM"),
            smtp_starttls=(
                os.getenv("AA_SMTP_STARTTLS", "true").lower()
                == "true"
            ),
        )