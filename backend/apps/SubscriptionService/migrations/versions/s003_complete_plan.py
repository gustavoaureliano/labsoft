"""Full-catalog plan is independent of each individual course grant."""
from alembic import op
import sqlalchemy as sa

revision = "s003"
down_revision = "s002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("complete_plan",
        sa.Column("user_id", sa.Uuid(), primary_key=True),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("method", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("next_billing_at", sa.DateTime()),
        sa.Column("attempt", sa.Integer(), nullable=False), schema="subscription")


def downgrade():
    op.drop_table("complete_plan", schema="subscription")
