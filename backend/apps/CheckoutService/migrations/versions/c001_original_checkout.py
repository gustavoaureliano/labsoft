"""Original checkout persistence with positional integer references."""
from alembic import op
import sqlalchemy as sa

revision = "c001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("checkout",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("idempotency_key", sa.String(), nullable=False, unique=True),
        sa.Column("request_hash", sa.String(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("method", sa.String(), nullable=False),
        sa.Column("plan", sa.String(), nullable=False),
        sa.Column("payment_id", sa.Integer()),
        sa.Column("created_at", sa.DateTime(), nullable=False), schema="checkout")


def downgrade():
    op.drop_table("checkout", schema="checkout")
