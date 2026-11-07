"""Canonical UUID users and optional course IDs for full plans."""
from alembic import op
import sqlalchemy as sa

revision = "c002"
down_revision = "c001"
branch_labels = None
depends_on = None


def require_empty():
    if op.get_bind().execute(sa.text("SELECT EXISTS (SELECT 1 FROM checkout.checkout)")).scalar():
        raise RuntimeError("Checkouts legados exigem mapa explícito de usuários e cursos antes de migrar.")


def upgrade():
    require_empty()
    for col in ("user_id", "item_id"):
        op.alter_column("checkout", col, type_=sa.Uuid(), existing_type=sa.Integer(),
                        postgresql_using=f"{col}::text::uuid", schema="checkout")
    op.alter_column("checkout", "item_id", nullable=True, existing_type=sa.Uuid(), schema="checkout")


def downgrade():
    require_empty()
    op.alter_column("checkout", "item_id", nullable=False, existing_type=sa.Uuid(), schema="checkout")
    for col in ("user_id", "item_id"):
        op.alter_column("checkout", col, type_=sa.Integer(), existing_type=sa.Uuid(),
                        postgresql_using=f"{col}::text::integer", schema="checkout")
