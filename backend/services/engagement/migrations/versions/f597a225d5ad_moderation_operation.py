"""Stable operation ID for retries and reopening moderation cases."""
from alembic import op
import sqlalchemy as sa

revision = "f597a225d5ad"
down_revision = "8b3d12c9a401"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("moderation_queue", sa.Column("operation_id", sa.String(36), nullable=True))
    op.execute("UPDATE moderation_queue SET operation_id = id WHERE length(id) = 36")


def downgrade():
    op.drop_column("moderation_queue", "operation_id")
