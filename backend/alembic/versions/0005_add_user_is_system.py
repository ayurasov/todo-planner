"""Add users.is_system flag (системный пользователь скрыт как исполнитель)

Revision ID: 0005_add_user_is_system
Revises: 0004_fix_global_role_constraint
Create Date: 2026-08-13 00:00:00.000000

admin помечает пользователя (например служебного admin-аккаунта или тестового
пользователя) как "системный" -- такой пользователь не должен предлагаться
в качестве исполнителя задачи, участника встречи, доступного пользователя
списка и т.п. (см. usersStore.assignable / useAssignableUsers на фронте).
В самом UsersView.vue системные пользователи всё равно видны и управляемы
администратором -- скрытие касается только мест выбора исполнителя/участника.

Прим.: add_column здесь без FK, поэтому обычный op.add_column тоже сработал
бы на SQLite, но используем batch_alter_table для единообразия с 0003/0004
и на случай будущих индексов/констрейнтов на этом поле.
"""

from alembic import op
import sqlalchemy as sa

revision = '0005_add_user_is_system'
down_revision = '0004_fix_global_role_constraint'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(
            sa.Column('is_system', sa.Boolean(), nullable=False, server_default=sa.false()),
        )


def downgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('is_system')
