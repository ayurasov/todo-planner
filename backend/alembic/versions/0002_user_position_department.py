"""Add position and department fields to users

Revision ID: 0002_user_position_department
Revises: 0001_initial_schema
Create Date: 2026-08-11 18:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = '0002_user_position_department'
down_revision = '0001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('position', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('department', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('users', 'department')
    op.drop_column('users', 'position')
