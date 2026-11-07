"""create daniel engagement, communication and moderation tables

Revision ID: 8b3d12c9a401
Revises: 45ac95d043fb
"""

from alembic import op
import sqlalchemy as sa


revision = "8b3d12c9a401"
down_revision = "45ac95d043fb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lesson_history",
        sa.Column("student_id", sa.String(length=255), nullable=False),
        sa.Column("lesson_id", sa.String(length=255), nullable=False),
        sa.Column(
            "viewed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("student_id", "lesson_id"),
    )
    op.create_index(
        "ix_lesson_history_student_viewed",
        "lesson_history",
        ["student_id", "viewed_at"],
        unique=False,
    )

    op.create_table(
        "lesson_favorites",
        sa.Column("student_id", sa.String(length=255), nullable=False),
        sa.Column("lesson_id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("student_id", "lesson_id"),
    )

    op.create_table(
        "playlists",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("student_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "name", name="uq_playlists_student_name"),
    )
    op.create_index(
        op.f("ix_playlists_student_id"), "playlists", ["student_id"], unique=False
    )

    op.create_table(
        "playlist_items",
        sa.Column("playlist_id", sa.String(length=255), nullable=False),
        sa.Column("lesson_id", sa.String(length=255), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "position >= 1", name="ck_playlist_items_position_positive"
        ),
        sa.ForeignKeyConstraint(["playlist_id"], ["playlists.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("playlist_id", "lesson_id"),
        sa.UniqueConstraint(
            "playlist_id", "position", name="uq_playlist_items_position"
        ),
    )

    op.create_table(
        "private_notes",
        sa.Column("student_id", sa.String(length=255), nullable=False),
        sa.Column("lesson_id", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("student_id", "lesson_id"),
    )

    op.create_table(
        "lesson_comments",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("lesson_id", sa.String(length=255), nullable=False),
        sa.Column("author_id", sa.String(length=255), nullable=False),
        sa.Column("author_name", sa.String(length=255), nullable=False),
        sa.Column("parent_id", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "moderation_status",
            sa.String(length=20),
            server_default="approved",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "moderation_status IN ('approved', 'held', 'hidden', 'deleted')",
            name="ck_lesson_comments_moderation_status",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"], ["lesson_comments.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_lesson_comments_author_id"),
        "lesson_comments",
        ["author_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lesson_comments_lesson_id"),
        "lesson_comments",
        ["lesson_id"],
        unique=False,
    )
    op.create_index(
        "ix_lesson_comments_lesson_status",
        "lesson_comments",
        ["lesson_id", "moderation_status"],
        unique=False,
    )

    op.create_table(
        "content_ratings",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("student_id", sa.String(length=255), nullable=False),
        sa.Column("target_type", sa.String(length=20), nullable=False),
        sa.Column("target_id", sa.String(length=255), nullable=False),
        sa.Column("stars", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "stars >= 1 AND stars <= 5", name="ck_content_ratings_stars_range"
        ),
        sa.CheckConstraint(
            "target_type IN ('lesson', 'course')",
            name="ck_content_ratings_target_type",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "student_id",
            "target_type",
            "target_id",
            name="uq_content_ratings_student_target",
        ),
    )
    op.create_index(
        op.f("ix_content_ratings_student_id"),
        "content_ratings",
        ["student_id"],
        unique=False,
    )
    op.create_index(
        "ix_content_ratings_target",
        "content_ratings",
        ["target_type", "target_id"],
        unique=False,
    )

    op.create_table(
        "questions",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("student_id", sa.String(length=255), nullable=False),
        sa.Column("student_name", sa.String(length=255), nullable=False),
        sa.Column("course_id", sa.String(length=255), nullable=False),
        sa.Column("lesson_id", sa.String(length=255), nullable=True),
        sa.Column("teacher_id", sa.String(length=255), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column(
            "status", sa.String(length=20), server_default="pending", nullable=False
        ),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'answered')", name="ck_questions_status"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_questions_course_id"), "questions", ["course_id"], unique=False
    )
    op.create_index(
        op.f("ix_questions_student_id"), "questions", ["student_id"], unique=False
    )
    op.create_index(
        "ix_questions_student_created",
        "questions",
        ["student_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_questions_teacher_id"), "questions", ["teacher_id"], unique=False
    )
    op.create_index(
        "ix_questions_teacher_status",
        "questions",
        ["teacher_id", "status"],
        unique=False,
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("destination_url", sa.String(length=512), nullable=False),
        sa.Column(
            "is_read", sa.Boolean(), server_default="false", nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_notifications_user_id"), "notifications", ["user_id"], unique=False
    )
    op.create_index(
        "ix_notifications_user_created",
        "notifications",
        ["user_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "content_reports",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("reporter_id", sa.String(length=255), nullable=False),
        sa.Column("item_type", sa.String(length=20), nullable=False),
        sa.Column("item_id", sa.String(length=255), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "status", sa.String(length=20), server_default="pending", nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "item_type IN ('lesson', 'course', 'comment')",
            name="ck_content_reports_item_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'resolved')", name="ck_content_reports_status"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "reporter_id",
            "item_type",
            "item_id",
            name="uq_content_reports_author_item",
        ),
    )
    op.create_index(
        op.f("ix_content_reports_reporter_id"),
        "content_reports",
        ["reporter_id"],
        unique=False,
    )
    op.create_index(
        "ix_content_reports_item_status",
        "content_reports",
        ["item_type", "item_id", "status"],
        unique=False,
    )

    op.create_table(
        "moderation_queue",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("item_type", sa.String(length=20), nullable=False),
        sa.Column("item_id", sa.String(length=255), nullable=False),
        sa.Column(
            "status", sa.String(length=20), server_default="pending", nullable=False
        ),
        sa.Column("decision", sa.String(length=20), nullable=True),
        sa.Column("admin_id", sa.String(length=255), nullable=True),
        sa.Column("justification", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "item_type IN ('lesson', 'course', 'comment')",
            name="ck_moderation_queue_item_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'kept', 'hidden', 'deleted')",
            name="ck_moderation_queue_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("item_type", "item_id", name="uq_moderation_queue_item"),
    )
    op.create_index(
        "ix_moderation_queue_status", "moderation_queue", ["status"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_moderation_queue_status", table_name="moderation_queue")
    op.drop_table("moderation_queue")
    op.drop_index("ix_content_reports_item_status", table_name="content_reports")
    op.drop_index(
        op.f("ix_content_reports_reporter_id"), table_name="content_reports"
    )
    op.drop_table("content_reports")
    op.drop_index("ix_notifications_user_created", table_name="notifications")
    op.drop_index(op.f("ix_notifications_user_id"), table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_questions_teacher_status", table_name="questions")
    op.drop_index(op.f("ix_questions_teacher_id"), table_name="questions")
    op.drop_index("ix_questions_student_created", table_name="questions")
    op.drop_index(op.f("ix_questions_student_id"), table_name="questions")
    op.drop_index(op.f("ix_questions_course_id"), table_name="questions")
    op.drop_table("questions")
    op.drop_index("ix_content_ratings_target", table_name="content_ratings")
    op.drop_index(
        op.f("ix_content_ratings_student_id"), table_name="content_ratings"
    )
    op.drop_table("content_ratings")
    op.drop_index(
        "ix_lesson_comments_lesson_status", table_name="lesson_comments"
    )
    op.drop_index(
        op.f("ix_lesson_comments_lesson_id"), table_name="lesson_comments"
    )
    op.drop_index(
        op.f("ix_lesson_comments_author_id"), table_name="lesson_comments"
    )
    op.drop_table("lesson_comments")
    op.drop_table("private_notes")
    op.drop_table("playlist_items")
    op.drop_index(op.f("ix_playlists_student_id"), table_name="playlists")
    op.drop_table("playlists")
    op.drop_table("lesson_favorites")
    op.drop_index(
        "ix_lesson_history_student_viewed", table_name="lesson_history"
    )
    op.drop_table("lesson_history")
