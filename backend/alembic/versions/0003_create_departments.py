"""Create departments table and manager_departments many-to-many link

Revision ID: 0003_create_departments
Revises: 0002_user_position_department
Create Date: 2026-08-12 06:40:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = '0003_create_departments'
down_revision = '0002_user_position_department'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'departments',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.Text(), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        'manager_departments',
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('department_id', sa.String(length=36), sa.ForeignKey('departments.id', ondelete='CASCADE'), primary_key=True),
    )
    op.add_column('users', sa.Column('department_id', sa.String(length=36), sa.ForeignKey('departments.id', ondelete='SET NULL'), nullable=True))
    op.add_column('lists', sa.Column('department_id', sa.String(length=36), sa.ForeignKey('departments.id', ondelete='SET NULL'), nullable=True))
    op.add_column('meetings', sa.Column('department_id', sa.String(length=36), sa.ForeignKey('departments.id', ondelete='SET NULL'), nullable=True))


def downgrade():
    op.drop_column('meetings', 'department_id')
    op.drop_column('lists', 'department_id')
    op.drop_column('users', 'department_id')
    op.drop_table('manager_departments')
    op.drop_table('departments')
