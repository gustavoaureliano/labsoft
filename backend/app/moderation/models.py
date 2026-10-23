"""Database models strictly required for ReportService and ContentModerationService (F28, F45)."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ContentReport(Base):
    """F28 — Enviar denúncia (impede duplicação do mesmo autor para o mesmo item)."""

    __tablename__ = "content_reports"
    __table_args__ = (
        CheckConstraint(
            "item_type IN ('lesson', 'course', 'comment')",
            name="ck_content_reports_item_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'resolved')",
            name="ck_content_reports_status",
        ),
        UniqueConstraint(
            "reporter_id",
            "item_type",
            "item_id",
            name="uq_content_reports_author_item",
        ),
        Index("ix_content_reports_item_status", "item_type", "item_id", "status"),
    )

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid4())
    )
    reporter_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)
    item_id: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="pending", server_default="pending", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ModerationQueueItem(Base):
    """F28, F45 — Fila de moderação de conteúdo e comentários e decisão administrativa."""

    __tablename__ = "moderation_queue"
    __table_args__ = (
        CheckConstraint(
            "item_type IN ('lesson', 'course', 'comment')",
            name="ck_moderation_queue_item_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'kept', 'hidden', 'deleted')",
            name="ck_moderation_queue_status",
        ),
        UniqueConstraint("item_type", "item_id", name="uq_moderation_queue_item"),
        Index("ix_moderation_queue_status", "status"),
    )

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid4())
    )
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)
    item_id: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="pending", server_default="pending", nullable=False
    )
    decision: Mapped[str | None] = mapped_column(String(20), nullable=True)
    admin_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
