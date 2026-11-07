"""complete catalog and course management backend

Revision ID: e8b7f4c2a1d0
Revises: cd5e7d4e16a9
"""

from alembic import op
import sqlalchemy as sa


revision = "e8b7f4c2a1d0"
down_revision = "cd5e7d4e16a9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "courses",
        sa.Column("teacher_name", sa.String(160), server_default="Professor", nullable=False),
    )
    op.add_column(
        "courses", sa.Column("area", sa.String(120), server_default="Geral", nullable=False)
    )
    op.add_column(
        "courses", sa.Column("featured", sa.Boolean(), server_default=sa.false(), nullable=False)
    )
    op.add_column(
        "courses", sa.Column("search_text", sa.Text(), server_default="", nullable=False)
    )
    op.add_column(
        "courses", sa.Column("view_count", sa.BigInteger(), server_default="0", nullable=False)
    )
    op.add_column("courses", sa.Column("published_at", sa.DateTime(timezone=True)))

    op.create_table(
        "course_lessons",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("course_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("summary", sa.Text(), server_default="", nullable=False),
        sa.Column("duration_minutes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("video_media_id", sa.Uuid()),
        sa.Column("preview_available", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("duration_minutes >= 0", name="ck_course_lessons_duration"),
        sa.CheckConstraint("position >= 0", name="ck_course_lessons_position"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["video_media_id"], ["media.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id", "position", name="uq_course_lessons_position"),
    )
    op.create_index("ix_course_lessons_course_id", "course_lessons", ["course_id"])

    op.create_table(
        "course_materials",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("course_id", sa.Uuid(), nullable=False),
        sa.Column("lesson_id", sa.Uuid()),
        sa.Column("media_id", sa.Uuid()),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("external_url", sa.String(2048)),
        sa.Column("access_level", sa.String(20), server_default="enrolled", nullable=False),
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("position >= 0", name="ck_course_materials_position"),
        sa.CheckConstraint(
            "access_level IN ('public', 'enrolled')",
            name="ck_course_materials_access_level",
        ),
        sa.CheckConstraint(
            "media_id IS NOT NULL OR external_url IS NOT NULL",
            name="ck_course_materials_source",
        ),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lesson_id"], ["course_lessons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["media_id"], ["media.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_course_materials_course_id", "course_materials", ["course_id"])
    op.create_index("ix_course_materials_lesson_id", "course_materials", ["lesson_id"])
    op.create_index("ix_course_materials_media_id", "course_materials", ["media_id"])

    op.create_table(
        "enrollments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("course_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(20), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "status IN ('active', 'completed', 'cancelled')",
            name="ck_enrollments_status",
        ),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id", "student_id", name="uq_enrollments_course_student"),
    )
    op.create_index("ix_enrollments_course_id", "enrollments", ["course_id"])
    op.create_index("ix_enrollments_student_id", "enrollments", ["student_id"])

    op.create_table(
        "course_reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("course_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column("comment", sa.Text(), server_default="", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_course_reviews_rating"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id", "student_id", name="uq_reviews_course_student"),
    )
    op.create_index("ix_course_reviews_course_id", "course_reviews", ["course_id"])
    op.create_index("ix_course_reviews_student_id", "course_reviews", ["student_id"])


def downgrade() -> None:
    op.drop_table("course_reviews")
    op.drop_table("enrollments")
    op.drop_table("course_materials")
    op.drop_table("course_lessons")
    op.drop_column("courses", "published_at")
    op.drop_column("courses", "view_count")
    op.drop_column("courses", "search_text")
    op.drop_column("courses", "featured")
    op.drop_column("courses", "area")
    op.drop_column("courses", "teacher_name")
