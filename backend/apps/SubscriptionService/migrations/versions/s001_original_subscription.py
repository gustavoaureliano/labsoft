"""Baseline of Joao's original persistence, before canonical ID adaptation."""
from alembic import op
import sqlalchemy as sa

revision = "s001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("subscription",
        sa.Column("user_id", sa.Integer(), primary_key=True),
        sa.Column("item_id", sa.Integer(), primary_key=True),
        sa.Column("plan", sa.String(), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("method", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("next_billing_at", sa.DateTime(), nullable=True),
        sa.Column("attempt", sa.Integer(), nullable=False), schema="subscription")
    op.create_table("processed_payment", sa.Column("payment_id", sa.Integer(), primary_key=True), schema="subscription")


def downgrade():
    op.drop_table("processed_payment", schema="subscription")
    op.drop_table("subscription", schema="subscription")
