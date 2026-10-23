from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _int_env(key: str, default: int) -> int:
    return int(os.environ.get(key, str(default)))


@dataclass(frozen=True)
class Settings:
    session_hours: int = 12
    jwt_secret: str = ""
    reset_minutes: int = 20
    media_root: Path = Path("./private_uploads")
    max_document_bytes: int = 8 * 1024 * 1024
    password_reset_url: str = (
        "http://localhost:5173/redefinir-senha"
    )
    frontend_origin: str = "http://localhost:3000"

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_starttls: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        jwt_secret = os.getenv("AA_JWT_SECRET", "").strip()
        if not jwt_secret:
            raise ValueError(
                "Configure AA_JWT_SECRET with a secure signing key."
            )
        if len(jwt_secret.encode("utf-8")) < 32:
            raise ValueError(
                "AA_JWT_SECRET must contain at least 32 bytes."
            )

        return cls(
            session_hours=_int_env("AA_SESSION_HOURS", 12),
            jwt_secret=jwt_secret,
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