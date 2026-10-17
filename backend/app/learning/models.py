from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Lesson(Base):
    __tablename__ = "lessons"
    __table_args__ = (
        CheckConstraint("position >= 1", name="ck_lessons_position_positive"),
        UniqueConstraint("course_id", "position", name="uq_lessons_course_position"),
    )

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid4()))
    course_id: Mapped[str] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    position: Mapped[int]
    media_id: Mapped[UUID | None] = mapped_column(ForeignKey("media.id"))
    thumbnail_id: Mapped[UUID | None] = mapped_column(ForeignKey("media.id", name="fk_lessons_thumbnail"))


class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    __table_args__ = (CheckConstraint("position_seconds >= 0", name="ck_progress_position"),)

    student_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True)
    media_id: Mapped[UUID] = mapped_column(ForeignKey("media.id"))
    position_seconds: Mapped[float] = mapped_column(Float)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
