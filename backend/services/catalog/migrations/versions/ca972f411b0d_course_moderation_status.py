"""Keep moderated courses and their historical references without publishing them."""
from alembic import op
import sqlalchemy as sa

revision = "ca972f411b0d"
down_revision = "b127f4cfa408"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("courses", sa.Column("moderation_status", sa.String(20), nullable=False,
                                       server_default="visible"))
    op.create_check_constraint("ck_courses_moderation_status", "courses",
                               "moderation_status IN ('visible', 'hidden', 'deleted')")


def downgrade():
    op.drop_constraint("ck_courses_moderation_status", "courses", type_="check")
    op.drop_column("courses", "moderation_status")
