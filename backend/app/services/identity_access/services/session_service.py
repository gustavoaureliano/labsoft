from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from jwt import InvalidTokenError
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import (
    AuthSession,
    RefreshToken,
    User,
    utcnow,
)
from ..security import (
    create_access_token,
    decode_access_token,
    generate_secret,
    token_digest,
)
from .errors import ServiceError


@dataclass(frozen=True)
class SessionTokens:
    access_token: str
    refresh_token: str
    expires_in_seconds: int
    session_id: str


class SessionService:

    def create(
        self,
        db: Session,
        user: User,
        settings: Settings,
    ) -> SessionTokens:
        now = utcnow()
        session_expires_at = now + timedelta(
            days=settings.refresh_token_days
        )
        session = AuthSession(
            user_id=user.id,
            expires_at=session_expires_at,
            last_activity_at=now,
        )
        db.add(session)
        db.flush()

        refresh_raw = generate_secret()
        refresh = RefreshToken(
            session_id=session.id,
            family_id=session.id,
            token_hash=token_digest(refresh_raw),
            expires_at=session_expires_at,
        )
        db.add(refresh)

        access_token, _ = create_access_token(
            user,
            session.id,
            settings,
        )
        return SessionTokens(
            access_token=access_token,
            refresh_token=refresh_raw,
            expires_in_seconds=(
                settings.access_token_minutes * 60
            ),
            session_id=session.id,
        )

    def authenticate(
        self,
        db: Session,
        raw_token: str,
        settings: Settings,
    ) -> User:
        try:
            claims = decode_access_token(
                raw_token,
                settings,
            )
        except InvalidTokenError as exc:
            raise ServiceError(
                "unauthorized",
                "Token inválido ou expirado.",
            ) from exc

        session = db.get(AuthSession, claims["sid"])
        user = db.get(User, claims["sub"])
        if (
            session is None
            or user is None
            or session.user_id != user.id
            or session.revoked_at is not None
            or session.expires_at <= utcnow()
            or not user.is_active
            or user.status != "active"
            or claims["ver"] != user.token_version
        ):
            raise ServiceError(
                "unauthorized",
                "Sessão ausente, expirada ou revogada.",
            )

        session.last_activity_at = utcnow()
        return user

    def refresh(
        self,
        db: Session,
        raw_token: str,
        settings: Settings,
    ) -> SessionTokens:
        refresh = db.scalar(
            select(RefreshToken)
            .where(
                RefreshToken.token_hash
                == token_digest(raw_token)
            )
            .with_for_update()
        )
        if refresh is None:
            raise ServiceError(
                "unauthorized",
                "Refresh token inválido ou expirado.",
            )

        session = db.get(AuthSession, refresh.session_id)
        user = (
            db.get(User, session.user_id)
            if session is not None
            else None
        )

        if refresh.used_at is not None or refresh.revoked_at is not None:
            if session is not None:
                self.revoke_session(db, session.id)
                db.commit()
            raise ServiceError(
                "unauthorized",
                "Reutilização de refresh token detectada.",
            )

        now = utcnow()
        if (
            refresh.expires_at <= now
            or session is None
            or session.revoked_at is not None
            or session.expires_at <= now
            or user is None
            or not user.is_active
            or user.status != "active"
        ):
            raise ServiceError(
                "unauthorized",
                "Refresh token inválido ou expirado.",
            )

        claimed = db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.id == refresh.id,
                RefreshToken.used_at.is_(None),
                RefreshToken.revoked_at.is_(None),
            )
            .values(used_at=now)
        )
        if claimed.rowcount != 1:
            self.revoke_session(db, session.id)
            db.commit()
            raise ServiceError(
                "unauthorized",
                "Reutilização de refresh token detectada.",
            )

        successor_raw = generate_secret()
        successor = RefreshToken(
            session_id=session.id,
            family_id=refresh.family_id,
            token_hash=token_digest(successor_raw),
            expires_at=now + timedelta(
                days=settings.refresh_token_days
            ),
        )
        db.add(successor)
        db.flush()
        refresh.replaced_by_id = successor.id

        session.expires_at = successor.expires_at
        session.last_activity_at = now
        access_token, _ = create_access_token(
            user,
            session.id,
            settings,
        )
        return SessionTokens(
            access_token=access_token,
            refresh_token=successor_raw,
            expires_in_seconds=(
                settings.access_token_minutes * 60
            ),
            session_id=session.id,
        )

    def create_admin_docs_token(
        self,
        user: User,
        session_id: str,
        settings: Settings,
    ) -> str:
        return create_access_token(
            user,
            session_id,
            settings,
            purpose="admin_docs",
        )[0]

    def authenticate_admin_docs(
        self,
        db: Session,
        token: str,
        settings: Settings,
    ) -> User:
        try:
            claims = decode_access_token(
                token,
                settings,
                expected_purpose="admin_docs",
            )
        except InvalidTokenError as exc:
            raise ServiceError(
                "unauthorized",
                "Sessão administrativa inválida ou expirada.",
            ) from exc

        session = db.get(AuthSession, claims["sid"])
        user = db.get(User, claims["sub"])
        if (
            session is None
            or user is None
            or session.user_id != user.id
            or session.revoked_at is not None
            or session.expires_at <= utcnow()
            or not user.is_active
            or user.status != "active"
            or user.role != "admin"
            or claims["ver"] != user.token_version
        ):
            raise ServiceError(
                "forbidden",
                "A documentação é restrita a administradores ativos.",
            )
        return user

    def revoke(
        self,
        db: Session,
        raw_token: str,
        settings: Settings,
    ) -> None:
        try:
            claims = decode_access_token(raw_token, settings)
        except InvalidTokenError as exc:
            raise ServiceError(
                "unauthorized",
                "Token inválido ou expirado.",
            ) from exc
        self.revoke_session(db, claims["sid"])

    def revoke_by_refresh_token(
        self,
        db: Session,
        raw_token: str,
    ) -> None:
        refresh = db.scalar(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_digest(raw_token)
            )
        )
        if refresh is None:
            raise ServiceError(
                "unauthorized",
                "Refresh token inválido.",
            )
        self.revoke_session(db, refresh.session_id)

    def revoke_session(
        self,
        db: Session,
        session_id: str,
    ) -> None:
        session = db.get(AuthSession, session_id)
        if session is None or session.revoked_at is not None:
            return
        now = utcnow()
        session.revoked_at = now
        db.execute(
            update(RefreshToken)
            .where(RefreshToken.session_id == session_id)
            .values(revoked_at=now)
        )

    def revoke_all(
        self,
        db: Session,
        user_id: str,
    ) -> None:
        now = utcnow()
        session_ids = list(
            db.scalars(
                select(AuthSession.id).where(
                    AuthSession.user_id == user_id,
                    AuthSession.revoked_at.is_(None),
                )
            )
        )
        db.execute(
            update(AuthSession)
            .where(AuthSession.id.in_(session_ids))
            .values(revoked_at=now)
        )
        db.execute(
            update(RefreshToken)
            .where(RefreshToken.session_id.in_(session_ids))
            .values(revoked_at=now)
        )

    def list_for_user(
        self,
        db: Session,
        user_id: str,
    ) -> list[AuthSession]:
        return list(
            db.scalars(
                select(AuthSession)
                .where(AuthSession.user_id == user_id)
                .order_by(AuthSession.created_at.desc())
            )
        )
