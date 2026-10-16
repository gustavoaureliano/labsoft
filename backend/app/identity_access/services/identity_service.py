from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import (
    User,
    AuthSession,
    PasswordReset,
    utcnow,
)
from ..schemas import RegisterIn
from ..security import (
    generate_secret,
    hash_password,
    token_digest,
    verify_password,
)
from .errors import ServiceError


class IdentityService:

    def register(
        self,
        db: Session,
        data: RegisterIn,
    ) -> User:

        email = str(data.email).strip().lower()

        existing = db.scalar(
            select(User.id).where(
                User.email == email
            )
        )

        if existing is not None:
            raise ServiceError(
                "conflict",
                "E-mail já cadastrado.",
            )

        user = User(
            email=email,
            password_hash=hash_password(data.password),
            role="student",
        )

        db.add(user)
        db.flush()

        return user

    def authenticate(
        self,
        db: Session,
        email: str,
        password: str,
    ) -> User:

        user = db.scalar(
            select(User).where(
                User.email == email.strip().lower()
            )
        )

        if (
            user is None
            or not user.is_active
            or not verify_password(
                user.password_hash, password
            )
        ):
            raise ServiceError(
                "unauthorized",
                "Credenciais inválidas.",
            )

        return user

    def request_password_reset(
        self,
        db: Session,
        email: str,
        settings: Settings,
    ) -> tuple[str, str] | None:

        user = db.scalar(
            select(User).where(
                User.email == email.strip().lower(),
                User.is_active.is_(True),
            )
        )

        if user is None:
            return None

        now = utcnow()

        db.execute(
            update(PasswordReset)
            .where(
                PasswordReset.user_id == user.id,
                PasswordReset.used_at.is_(None),
            )
            .values(used_at=now)
        )

        raw = generate_secret()

        db.add(
            PasswordReset(
                user_id=user.id,
                token_hash=token_digest(raw),
                expires_at=now + timedelta(
                    minutes=settings.reset_minutes
                ),
            )
        )

        db.flush()

        return user.email, raw

    def reset_password(
        self,
        db: Session,
        raw_token: str,
        new_password: str,
    ) -> None:

        entry = db.scalar(
            select(PasswordReset).where(
                PasswordReset.token_hash
                == token_digest(raw_token)
            )
        )

        now = utcnow()

        if (
            entry is None
            or entry.used_at is not None
            or entry.expires_at <= now
        ):
            raise ServiceError(
                "invalid",
                "Código de recuperação inválido, "
                "expirado ou já utilizado.",
            )

        claim = db.execute(
            update(PasswordReset)
            .where(
                PasswordReset.id == entry.id,
                PasswordReset.used_at.is_(None),
                PasswordReset.expires_at > now,
            )
            .values(used_at=now)
        )

        if claim.rowcount != 1:
            raise ServiceError(
                "invalid",
                "Código de recuperação já utilizado.",
            )

        user = db.get(User, entry.user_id)

        if user is None or not user.is_active:
            raise ServiceError(
                "invalid",
                "Código de recuperação inválido.",
            )

        user.password_hash = hash_password(
            new_password
        )

        db.execute(
            update(PasswordReset)
            .where(
                PasswordReset.user_id == user.id,
                PasswordReset.used_at.is_(None),
            )
            .values(used_at=now)
        )

        db.execute(
            update(AuthSession)
            .where(
                AuthSession.user_id == user.id,
                AuthSession.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )

        db.flush()

    @staticmethod
    def require_roles(
        user: User,
        *roles: str,
    ) -> None:

        if not user.is_active:
            raise ServiceError(
                "unauthorized",
                "Conta desativada.",
            )

        if user.role not in roles:
            raise ServiceError(
                "forbidden",
                "Seu perfil não possui permissão "
                "para esta ação.",
            )

    @staticmethod
    def require_owner(
        user: User,
        resource_owner_id: str,
        allow_admin: bool = False,
    ) -> None:

        if not user.is_active:
            raise ServiceError(
                "unauthorized",
                "Conta desativada.",
            )

        if (
            user.id != resource_owner_id
            and not (
                allow_admin
                and user.role == "admin"
            )
        ):
            raise ServiceError(
                "forbidden",
                "Você não possui acesso "
                "a este recurso.",
            )