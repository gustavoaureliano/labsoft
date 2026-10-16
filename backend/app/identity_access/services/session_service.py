from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import (
    AuthSession,
    User,
    utcnow,
)
from ..security import (
    generate_secret,
    token_digest,
)
from .errors import ServiceError


class SessionService:

    def create(
        self,
        db: Session,
        user: User,
        settings: Settings,
    ) -> str:

        raw = generate_secret()

        session = AuthSession(
            user_id=user.id,
            token_hash=token_digest(raw),
            expires_at=utcnow() + timedelta(
                hours=settings.session_hours
            ),
        )

        db.add(session)
        db.flush()

        return raw

    def authenticate(
        self,
        db: Session,
        raw_token: str,
    ) -> User:

        session = db.scalar(
            select(AuthSession).where(
                AuthSession.token_hash
                == token_digest(raw_token)
            )
        )

        if (
            session is None
            or session.revoked_at is not None
            or session.expires_at <= utcnow()
        ):
            raise ServiceError(
                "unauthorized",
                "Sessão ausente, expirada ou revogada.",
            )

        user = db.get(
            User, session.user_id
        )

        if user is None or not user.is_active:
            raise ServiceError(
                "unauthorized",
                "Usuário não está ativo.",
            )

        return user

    def revoke(
        self,
        db: Session,
        raw_token: str,
    ) -> None:

        session = db.scalar(
            select(AuthSession).where(
                AuthSession.token_hash
                == token_digest(raw_token)
            )
        )

        if (
            session is None
            or session.revoked_at is not None
        ):
            raise ServiceError(
                "unauthorized",
                "Sessão inválida.",
            )

        session.revoked_at = utcnow()
        db.flush()