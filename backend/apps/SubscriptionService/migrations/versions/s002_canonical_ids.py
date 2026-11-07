"""Canonical user/course UUIDs; no guessing a map from catalog positions."""
from alembic import op
import sqlalchemy as sa

revision = "s002"
down_revision = "s001"
branch_labels = None
depends_on = None


def require_empty():
    if op.get_bind().execute(sa.text("SELECT EXISTS (SELECT 1 FROM subscription.subscription)")).scalar():
        raise RuntimeError("Migração de IDs exige mapa explícito para dados existentes; não converter índices automaticamente.")


def upgrade():
    require_empty()
    for column in ("user_id", "item_id"):
        op.alter_column("subscription", column, type_=sa.Uuid(), existing_type=sa.Integer(),
                        postgresql_using=f"{column}::text::uuid", schema="subscription")


def downgrade():
    require_empty()
    for column in ("user_id", "item_id"):
        op.alter_column("subscription", column, type_=sa.Integer(), existing_type=sa.Uuid(),
                        postgresql_using=f"{column}::text::integer", schema="subscription")
