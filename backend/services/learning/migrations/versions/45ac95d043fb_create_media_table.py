"""Create media table

Revision ID: 45ac95d043fb
Revises: None
"""

from alembic import op
import sqlalchemy as sa


revision = "45ac95d043fb"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "media",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'available', 'failed')", name="ck_media_status",
        ),
        sa.CheckConstraint("size_bytes >= 0", name="ck_media_size_nonnegative"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
    )


def downgrade() -> None:
    op.drop_table("media")
