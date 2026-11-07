"""Create lessons table

Revision ID: 459d40bd6106
Revises: 45ac95d043fb
"""

from alembic import op
import sqlalchemy as sa


revision = '459d40bd6106'
down_revision = '45ac95d043fb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'lessons',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('course_id', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('media_id', sa.Uuid(), nullable=True),
        sa.CheckConstraint('position >= 1', name='ck_lessons_position_positive'),
        sa.ForeignKeyConstraint(['media_id'], ['media.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('course_id', 'position', name='uq_lessons_course_position'),
    )
    op.create_index(op.f('ix_lessons_course_id'), 'lessons', ['course_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_lessons_course_id'), table_name='lessons')
    op.drop_table('lessons')
