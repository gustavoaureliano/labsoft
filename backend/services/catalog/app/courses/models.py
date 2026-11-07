"""Database models for catalog, course management, and access control."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (
        CheckConstraint("access_type IN ('free', 'paid')", name="ck_courses_access_type"),
        CheckConstraint(
            "status IN ('draft', 'published', 'archived')",
            name="ck_courses_status",
        ),
        CheckConstraint(
            """
            (access_type = 'free' AND (price IS NULL OR price = 0))
            OR
            (access_type = 'paid' AND price > 0)
            """,
            name="ck_courses_access_price",
        ),
        Index("ix_courses_teacher_status", "teacher_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    # Replaced by a ForeignKey when the authentication/user module is integrated.
    teacher_id: Mapped[UUID] = mapped_column(index=True, nullable=False)
    teacher_name: Mapped[str] = mapped_column(
        String(160), default="Professor", server_default="Professor", nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    subject: Mapped[str] = mapped_column(String(120), nullable=False)
    area: Mapped[str] = mapped_column(
        String(120), default="Geral", server_default="Geral", nullable=False
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    exams: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    access_type: Mapped[str] = mapped_column(String(10), nullable=False)
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    cover_media_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("media.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default="draft", server_default="draft", nullable=False
    )
    featured: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    search_text: Mapped[str] = mapped_column(
        Text, default="", server_default="", nullable=False
    )
    view_count: Mapped[int] = mapped_column(
        BigInteger, default=0, server_default="0", nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class CourseLesson(Base):
    __tablename__ = "course_lessons"
    __table_args__ = (
        CheckConstraint("duration_minutes >= 0", name="ck_course_lessons_duration"),
        CheckConstraint("position >= 0", name="ck_course_lessons_position"),
        UniqueConstraint("course_id", "position", name="uq_course_lessons_position"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    course_id: Mapped[UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", server_default="", nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    video_media_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("media.id", ondelete="SET NULL")
    )
    preview_available: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class CourseMaterial(Base):
    __tablename__ = "course_materials"
    __table_args__ = (
        CheckConstraint("position >= 0", name="ck_course_materials_position"),
        CheckConstraint(
            "access_level IN ('public', 'enrolled')",
            name="ck_course_materials_access_level",
        ),
        CheckConstraint(
            "media_id IS NOT NULL OR external_url IS NOT NULL",
            name="ck_course_materials_source",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    course_id: Mapped[UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    lesson_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("course_lessons.id", ondelete="CASCADE"), index=True
    )
    media_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("media.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", server_default="", nullable=False)
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    external_url: Mapped[str | None] = mapped_column(String(2048))
    access_level: Mapped[str] = mapped_column(
        String(20), default="enrolled", server_default="enrolled", nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'completed', 'cancelled')",
            name="ck_enrollments_status",
        ),
        UniqueConstraint("course_id", "student_id", name="uq_enrollments_course_student"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    course_id: Mapped[UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    student_id: Mapped[UUID] = mapped_column(index=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="active", server_default="active", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CourseReview(Base):
    __tablename__ = "course_reviews"
    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_course_reviews_rating"),
        UniqueConstraint("course_id", "student_id", name="uq_reviews_course_student"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    course_id: Mapped[UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    student_id: Mapped[UUID] = mapped_column(index=True, nullable=False)
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    comment: Mapped[str] = mapped_column(Text, default="", server_default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
