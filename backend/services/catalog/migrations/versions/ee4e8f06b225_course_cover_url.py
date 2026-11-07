"""Keep the published course cover with its canonical catalog metadata."""
from alembic import op
import sqlalchemy as sa

revision = "ee4e8f06b225"
down_revision = "ca972f411b0d"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("courses", sa.Column("cover_url", sa.String(255), nullable=True))


def downgrade():
    op.drop_column("courses", "cover_url")
