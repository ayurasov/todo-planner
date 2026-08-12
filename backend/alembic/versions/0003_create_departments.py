"""Create departments table and manager_departments many-to-many link

Revision ID: 0003_create_departments
Revises: 0002_user_position_department
Create Date: 2026-08-12 06:40:00.000000

Прим.: добавление FK-колонок (department_id) в уже существующие таблицы
(users/lists/meetings) выполняется через batch_alter_table -- обычный
op.add_column(..., sa.ForeignKey(...)) не работает на SQLite, так как SQLite
не поддерживает ALTER TABLE ADD CONSTRAINT (см. NotImplementedError:
"No support for ALTER of constraints in SQLite dialect"). Batch mode
использует стратегию copy-and-move и одинаково корректно работает как на
SQLite (dev/test), так и на PostgreSQL (production) -- на Postgres batch
mode прозрачно выполняет обычный ALTER, без пересборки таблицы.
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

    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('department_id', sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            'fk_users_department_id_departments', 'departments', ['department_id'], ['id'], ondelete='SET NULL',
        )

    with op.batch_alter_table('lists') as batch_op:
        batch_op.add_column(sa.Column('department_id', sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            'fk_lists_department_id_departments', 'departments', ['department_id'], ['id'], ondelete='SET NULL',
        )

    with op.batch_alter_table('meetings') as batch_op:
        batch_op.add_column(sa.Column('department_id', sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            'fk_meetings_department_id_departments', 'departments', ['department_id'], ['id'], ondelete='SET NULL',
        )


def downgrade():
    with op.batch_alter_table('meetings') as batch_op:
        batch_op.drop_constraint('fk_meetings_department_id_departments', type_='foreignkey')
        batch_op.drop_column('department_id')

    with op.batch_alter_table('lists') as batch_op:
        batch_op.drop_constraint('fk_lists_department_id_departments', type_='foreignkey')
        batch_op.drop_column('department_id')

    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_constraint('fk_users_department_id_departments', type_='foreignkey')
        batch_op.drop_column('department_id')

    op.drop_table('manager_departments')
    op.drop_table('departments')
