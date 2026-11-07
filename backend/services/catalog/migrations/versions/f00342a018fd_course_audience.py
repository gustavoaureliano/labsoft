"""Store the intended audience with the canonical course."""
from alembic import op
import sqlalchemy as sa

revision = "f00342a018fd"
down_revision = "ee4e8f06b225"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("courses", sa.Column("audience", sa.Text(), nullable=False,
                                     server_default="Estudantes de vestibular"))


def downgrade():
    op.drop_column("courses", "audience")
