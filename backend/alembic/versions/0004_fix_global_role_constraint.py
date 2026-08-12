"""Fix ck_users_global_role check constraint to allow 'manager'

Revision ID: 0004_fix_global_role_constraint
Revises: 0003_create_departments
Create Date: 2026-08-12 13:00:00.000000

Context (incident): POST /api/users with globalRole='manager' raised a 500
(psycopg2.errors.CheckViolation: ck_users_global_role) because the original
check constraint from 0001_initial_schema only allowed ('admin', 'user').
The 'manager' role (руководитель отдела/службы, see ManagerDepartmentORM /
permission_service.py) was introduced later at the application layer but the
DB constraint was never updated to match.
"""

from alembic import op

revision = '0004_fix_global_role_constraint'
down_revision = '0003_create_departments'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('ck_users_global_role', 'users', type_='check')
    op.create_check_constraint(
        'ck_users_global_role',
        'users',
        "global_role IN ('admin', 'manager', 'user')",
    )


def downgrade():
    op.drop_constraint('ck_users_global_role', 'users', type_='check')
    op.create_check_constraint(
        'ck_users_global_role',
        'users',
        "global_role IN ('admin', 'user')",
    )
