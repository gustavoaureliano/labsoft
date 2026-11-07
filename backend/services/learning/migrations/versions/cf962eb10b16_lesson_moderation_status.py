"""Preserve moderated lessons and their progress without exposing playback."""
from alembic import op
import sqlalchemy as sa

revision = "cf962eb10b16"
down_revision = "3f1b59e6f5de"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("lessons", sa.Column("moderation_status", sa.String(20), nullable=False,
                                       server_default="visible"))
    op.create_check_constraint("ck_lessons_moderation_status", "lessons",
                               "moderation_status IN ('visible', 'hidden', 'deleted')")


def downgrade():
    op.drop_constraint("ck_lessons_moderation_status", "lessons", type_="check")
    op.drop_column("lessons", "moderation_status")
