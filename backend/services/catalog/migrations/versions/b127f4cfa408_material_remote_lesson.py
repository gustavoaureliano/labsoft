"""Reference lessons by Gustavo's canonical UUID, not the local duplicate table."""
from alembic import op
import sqlalchemy as sa

revision = "b127f4cfa408"
down_revision = "e8b7f4c2a1d0"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    if connection.execute(sa.text("SELECT EXISTS (SELECT 1 FROM course_materials WHERE lesson_id IS NOT NULL)")).scalar():
        raise RuntimeError("Materiais ligados a aulas locais exigem um mapa explícito para IDs de Gustavo.")
    op.drop_constraint("course_materials_lesson_id_fkey", "course_materials", type_="foreignkey")


def downgrade():
    connection = op.get_bind()
    if connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM course_materials m
            WHERE m.lesson_id IS NOT NULL
              AND NOT EXISTS (SELECT 1 FROM course_lessons l WHERE l.id = m.lesson_id)
        )
    """)).scalar():
        raise RuntimeError("Materiais ligados a aulas remotas não podem voltar à FK local.")
    op.create_foreign_key("course_materials_lesson_id_fkey", "course_materials", "course_lessons",
                          ["lesson_id"], ["id"], ondelete="CASCADE")
