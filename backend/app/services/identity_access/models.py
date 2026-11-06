from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.dbbase import Base


def utcnow() -> datetime:
    return datetime.now(
        timezone.utc
    ).replace(tzinfo=None)


def uuid_str() -> str:
    return str(uuid4())


class User(Base):
    __tablename__ = "aa_users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('student', 'teacher', 'admin')",
            name="ck_aa_users_role",
        ),
        CheckConstraint(
            "status IN ('pending_verification', 'active', 'suspended', 'disabled')",
            name="ck_aa_users_status",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=uuid_str,
    )

    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="student",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="active",
        index=True,
    )

    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime,
    )

    token_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
        nullable=False,
    )


class Profile(Base):
    __tablename__ = "aa_profiles"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("aa_users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    display_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    preferences: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    avatar_url: Mapped[str | None] = mapped_column(
        String(1024)
    )

    user: Mapped[User] = relationship()


class AuthSession(Base):
    __tablename__ = "aa_sessions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=uuid_str,
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("aa_users.id", ondelete="CASCADE"),
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime
    )

    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
        nullable=False,
    )

    user: Mapped[User] = relationship()


class RefreshToken(Base):
    __tablename__ = "aa_refresh_tokens"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=uuid_str,
    )

    session_id: Mapped[str] = mapped_column(
        ForeignKey("aa_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    family_id: Mapped[str] = mapped_column(
        String(36),
        index=True,
        nullable=False,
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    used_at: Mapped[datetime | None] = mapped_column(
        DateTime,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime,
    )

    replaced_by_id: Mapped[str | None] = mapped_column(
        ForeignKey("aa_refresh_tokens.id"),
    )


class EmailToken(Base):
    __tablename__ = "aa_email_tokens"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=uuid_str,
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("aa_users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    purpose: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
    )


class EmailOutbox(Base):
    __tablename__ = "aa_email_outbox"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=uuid_str,
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("aa_users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    recipient: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )

    purpose: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    encrypted_token: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )

    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
        nullable=False,
    )

    next_attempt_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
        nullable=False,
    )

    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime,
    )

    last_error: Mapped[str | None] = mapped_column(
        String(500),
    )

    idempotency_key: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default=uuid_str,
    )


class AuditEvent(Base):
    __tablename__ = "aa_audit_events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=uuid_str,
    )

    actor_id: Mapped[str | None] = mapped_column(
        ForeignKey("aa_users.id", ondelete="SET NULL"),
        index=True,
    )

    subject_id: Mapped[str | None] = mapped_column(
        ForeignKey("aa_users.id", ondelete="SET NULL"),
        index=True,
    )

    event: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    outcome: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    request_id: Mapped[str | None] = mapped_column(
        String(100),
        index=True,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
        nullable=False,
    )

    details: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )


class RateLimitBucket(Base):
    __tablename__ = "aa_rate_limit_buckets"

    key_hash: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )

    window_started_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )


class PasswordReset(Base):
    __tablename__ = "aa_password_resets"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=uuid_str,
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("aa_users.id", ondelete="CASCADE"),
        index=True,
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    used_at: Mapped[datetime | None] = mapped_column(
        DateTime
    )


class Notification(Base):
    __tablename__ = "aa_notifications"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=uuid_str,
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("aa_users.id", ondelete="CASCADE"),
        index=True,
    )

    category: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        String(600),
        nullable=False,
    )

    details: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
        nullable=False,
    )

    read_at: Mapped[datetime | None] = mapped_column(
        DateTime
    )


class TeacherApplication(Base):
    __tablename__ = "aa_teacher_applications"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            name="uq_aa_teacher_application_user",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=uuid_str,
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("aa_users.id", ondelete="CASCADE"),
        index=True,
    )

    legal_name: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    professional_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    expertise: Mapped[str] = mapped_column(
        String(240),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
        nullable=False,
    )

    documents: Mapped[list["MediaItem"]] = relationship(
        back_populates="application"
    )


class MediaItem(Base):
    __tablename__ = "aa_media"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=uuid_str,
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("aa_users.id", ondelete="CASCADE"),
        index=True,
    )

    application_id: Mapped[str | None] = mapped_column(
        ForeignKey(
            "aa_teacher_applications.id",
            ondelete="SET NULL",
        ),
        index=True,
    )

    original_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    storage_name: Mapped[str] = mapped_column(
        String(80),
        unique=True,
        nullable=False,
    )

    content_type: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
    )

    size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    checksum_sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
        nullable=False,
    )

    application: Mapped[
        TeacherApplication | None
    ] = relationship(
        back_populates="documents"
    )