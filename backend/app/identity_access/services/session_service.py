from __future__ import annotations

from datetime import timedelta

from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import (
    AuthSession,
    User,
    utcnow,
)
from ..security import (
    create_access_token,
    decode_access_token,
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

        expires_at = utcnow() + timedelta(
            hours=settings.session_hours
        )
        raw = create_access_token(
            user.id,
            settings.jwt_secret,
            expires_at,
        )

        session = AuthSession(
            user_id=user.id,
            token_hash=token_digest(raw),
            expires_at=expires_at,
        )

        db.add(session)
        db.flush()

        return raw

    def authenticate(
        self,
        db: Session,
        raw_token: str,
        settings: Settings | None = None,
    ) -> User:
        settings = settings or Settings.from_env()

        try:
            subject = decode_access_token(
                raw_token,
                settings.jwt_secret,
            )
        except InvalidTokenError as exc:
            raise ServiceError(
                "unauthorized",
                "Token inválido ou expirado.",
            ) from exc

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
            or session.user_id != subject
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