from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, String, Text, UniqueConstraint
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
