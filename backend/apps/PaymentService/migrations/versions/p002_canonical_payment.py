"""UUID users and optional course for a full-catalog subscription."""
from alembic import op
import sqlalchemy as sa

revision = "p002"
down_revision = "p001"
branch_labels = None
depends_on = None


def require_empty():
    if op.get_bind().execute(sa.text("SELECT EXISTS (SELECT 1 FROM payment.payment)")).scalar():
        raise RuntimeError("Pagamentos legados exigem mapa explícito de usuários e cursos.")


def upgrade():
    require_empty()
    for column in ("user_id", "item_id"):
        op.alter_column("payment", column, type_=sa.Uuid(), existing_type=sa.Integer(),
                        postgresql_using=f"{column}::text::uuid", schema="payment")
    op.alter_column("payment", "item_id", nullable=True, existing_type=sa.Uuid(), schema="payment")


def downgrade():
    require_empty()
    op.alter_column("payment", "item_id", nullable=False, existing_type=sa.Uuid(), schema="payment")
    for column in ("user_id", "item_id"):
        op.alter_column("payment", column, type_=sa.Integer(), existing_type=sa.Uuid(),
                        postgresql_using=f"{column}::text::integer", schema="payment")
