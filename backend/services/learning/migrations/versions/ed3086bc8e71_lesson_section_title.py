"""Persist the teacher's section title on each canonical lesson."""
from alembic import op
import sqlalchemy as sa

revision = "ed3086bc8e71"
down_revision = "cf962eb10b16"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("lessons", sa.Column("section_title", sa.String(120), nullable=False,
                                      server_default="Aulas do curso"))


def downgrade():
    op.drop_column("lessons", "section_title")
