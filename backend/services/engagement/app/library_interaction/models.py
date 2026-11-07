"""Database models strictly required for StudyLibraryService and LessonInteractionService (F21-F26)."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LessonHistory(Base):
    """F21 — Consultar histórico."""

    __tablename__ = "lesson_history"
    __table_args__ = (Index("ix_lesson_history_student_viewed", "student_id", "viewed_at"),)

    student_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    lesson_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class LessonFavorite(Base):
    """F22 — Gerenciar favoritos (PK composta garante ausência de duplicidade)."""

    __tablename__ = "lesson_favorites"

    student_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    lesson_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Playlist(Base):
    """F23 — Gerenciar playlists privadas do aluno."""

    __tablename__ = "playlists"
    __table_args__ = (
        UniqueConstraint("student_id", "name", name="uq_playlists_student_name"),
    )

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid4())
    )
    student_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class PlaylistItem(Base):
    """F23 — Vínculo e ordem das aulas dentro de uma playlist."""

    __tablename__ = "playlist_items"
    __table_args__ = (
        CheckConstraint("position >= 1", name="ck_playlist_items_position_positive"),
        UniqueConstraint("playlist_id", "position", name="uq_playlist_items_position"),
    )

    playlist_id: Mapped[str] = mapped_column(
        ForeignKey("playlists.id", ondelete="CASCADE"), primary_key=True
    )
    lesson_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)


class PrivateNote(Base):
    """F24 — Criar anotações privadas vinculadas ao aluno e à aula."""

    __tablename__ = "private_notes"

    student_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    lesson_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class LessonComment(Base):
    """F25 — Comentar uma aula (com suporte a respostas e estado de moderação)."""

    __tablename__ = "lesson_comments"
    __table_args__ = (
        CheckConstraint(
            "moderation_status IN ('approved', 'held', 'hidden', 'deleted')",
            name="ck_lesson_comments_moderation_status",
        ),
        Index("ix_lesson_comments_lesson_status", "lesson_id", "moderation_status"),
    )

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid4())
    )
    lesson_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    author_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    author_name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[str | None] = mapped_column(
        ForeignKey("lesson_comments.id", ondelete="CASCADE"), nullable=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    moderation_status: Mapped[str] = mapped_column(
        String(20), default="approved", server_default="approved", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ContentRating(Base):
    """F26 — Avaliar uma aula ou curso (1 avaliação por aluno e conteúdo)."""

    __tablename__ = "content_ratings"
    __table_args__ = (
        CheckConstraint(
            "target_type IN ('lesson', 'course')",
            name="ck_content_ratings_target_type",
        ),
        CheckConstraint(
            "stars >= 1 AND stars <= 5",
            name="ck_content_ratings_stars_range",
        ),
        UniqueConstraint(
            "student_id",
            "target_type",
            "target_id",
            name="uq_content_ratings_student_target",
        ),
        Index("ix_content_ratings_target", "target_type", "target_id"),
    )

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid4())
    )
    student_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    target_type: Mapped[str] = mapped_column(String(20), nullable=False)
    target_id: Mapped[str] = mapped_column(String(255), nullable=False)
    stars: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
