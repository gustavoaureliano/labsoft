from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import (
    User,
    AuthSession,
    EmailToken,
    PasswordReset,
    RefreshToken,
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
            is_active=False,
            status="pending_verification",
        )

        db.add(user)
        db.flush()

        return user

    def find_pending_user(
        self,
        db: Session,
        email: str,
    ) -> User | None:
        return db.scalar(
            select(User).where(
                User.email == email.strip().lower(),
                User.status == "pending_verification",
            )
        )

    def create_verification_token(
        self,
        db: Session,
        user: User,
        settings: Settings,
    ) -> str:
        now = utcnow()
        db.execute(
            update(EmailToken)
            .where(
                EmailToken.user_id == user.id,
                EmailToken.purpose == "verify_email",
                EmailToken.consumed_at.is_(None),
            )
            .values(consumed_at=now)
        )
        token = generate_secret()
        db.add(
            EmailToken(
                user_id=user.id,
                purpose="verify_email",
                token_hash=token_digest(token),
                expires_at=now + timedelta(
                    hours=settings.verification_hours
                ),
            )
        )
        db.flush()
        return token

    def verify_email(
        self,
        db: Session,
        raw_token: str,
    ) -> User:
        now = utcnow()
        entry = db.scalar(
            select(EmailToken).where(
                EmailToken.token_hash == token_digest(raw_token),
                EmailToken.purpose == "verify_email",
            )
        )
        if (
            entry is None
            or entry.consumed_at is not None
            or entry.expires_at <= now
        ):
            raise ServiceError(
                "invalid",
                "Token de confirmação inválido, expirado ou já utilizado.",
            )

        claim = db.execute(
            update(EmailToken)
            .where(
                EmailToken.id == entry.id,
                EmailToken.consumed_at.is_(None),
                EmailToken.expires_at > now,
            )
            .values(consumed_at=now)
        )
        if claim.rowcount != 1:
            raise ServiceError(
                "invalid",
                "Token de confirmação já utilizado.",
            )

        user = db.get(User, entry.user_id)
        if user is None or user.status != "pending_verification":
            raise ServiceError(
                "invalid",
                "A conta não está aguardando confirmação.",
            )

        user.status = "active"
        user.is_active = True
        user.verified_at = now
        db.flush()
        return user

    def set_role(
        self,
        db: Session,
        user_id: str,
        role: str,
    ) -> User:
        if role not in {"student", "teacher", "admin"}:
            raise ServiceError(
                "invalid",
                "Papel inválido.",
            )

        user = db.get(User, user_id)
        if user is None:
            raise ServiceError(
                "not_found",
                "Usuário não encontrado.",
            )
        if user.role != role:
            user.role = role
            user.token_version += 1
            active_sessions = list(
                db.scalars(
                    select(AuthSession.id).where(
                        AuthSession.user_id == user.id,
                        AuthSession.revoked_at.is_(None),
                    )
                )
            )
            db.execute(
                update(AuthSession)
                .where(AuthSession.id.in_(active_sessions))
                .values(revoked_at=utcnow())
            )
            db.execute(
                update(RefreshToken)
                .where(RefreshToken.session_id.in_(active_sessions))
                .values(revoked_at=utcnow())
            )
        db.flush()
        return user

    def set_status(
        self,
        db: Session,
        user_id: str,
        status: str,
    ) -> User:
        if status not in {"active", "suspended", "disabled"}:
            raise ServiceError("invalid", "Status inválido.")
        user = db.get(User, user_id)
        if user is None:
            raise ServiceError(
                "not_found",
                "Usuário não encontrado.",
            )
        if status == "active" and user.verified_at is None:
            raise ServiceError(
                "conflict",
                "A conta precisa confirmar o e-mail antes da ativação.",
            )
        if user.status != status:
            user.status = status
            user.is_active = status == "active"
            user.token_version += 1
            session_ids = list(
                db.scalars(
                    select(AuthSession.id).where(
                        AuthSession.user_id == user.id,
                        AuthSession.revoked_at.is_(None),
                    )
                )
            )
            revoked_at = utcnow()
            db.execute(
                update(AuthSession)
                .where(AuthSession.id.in_(session_ids))
                .values(revoked_at=revoked_at)
            )
            db.execute(
                update(RefreshToken)
                .where(RefreshToken.session_id.in_(session_ids))
                .values(revoked_at=revoked_at)
            )
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
            or user.status != "active"
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
    ) -> tuple[str, str, str] | None:

        user = db.scalar(
            select(User).where(
                User.email == email.strip().lower(),
                User.is_active.is_(True),
                User.status == "active",
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

        return user.email, raw, user.id

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
        user.token_version += 1

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
        db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.session_id.in_(
                    select(AuthSession.id).where(
                        AuthSession.user_id == user.id
                    )
                )
            )
            .values(revoked_at=now)
        )

        db.flush()

    @staticmethod
    def require_roles(
        user: User,
        *roles: str,
    ) -> None:

        if not user.is_active or user.status != "active":
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

        if not user.is_active or user.status != "active":
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