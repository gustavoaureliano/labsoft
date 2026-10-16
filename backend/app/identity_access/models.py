from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


def utcnow() -> datetime:
    return datetime.now(
        timezone.utc
    ).replace(tzinfo=None)


def uuid_str() -> str:
    return str(uuid4())


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "aa_users"

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

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime
    )

    user: Mapped[User] = relationship()


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