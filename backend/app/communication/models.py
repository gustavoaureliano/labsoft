"""Database models strictly required for QuestionService and NotificationService (F29-F32)."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Question(Base):
    """F29, F30, F31 — Dúvida privada entre aluno e professor responsável pelo curso."""

    __tablename__ = "questions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'answered')",
            name="ck_questions_status",
        ),
        Index("ix_questions_teacher_status", "teacher_id", "status"),
        Index("ix_questions_student_created", "student_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid4())
    )
    student_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    student_name: Mapped[str] = mapped_column(String(255), nullable=False)
    course_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    lesson_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    teacher_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="pending", server_default="pending", nullable=False
    )
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    answered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class Notification(Base):
    """F32 — Avisos e notificações do usuário (aluno, professor ou admin)."""

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_created", "user_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    destination_url: Mapped[str] = mapped_column(String(512), nullable=False)
    is_read: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
