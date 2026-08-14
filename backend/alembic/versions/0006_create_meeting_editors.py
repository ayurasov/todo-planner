"""Create meeting_editors table (MeetingEditorORM)

Revision ID: 0006_create_meeting_editors
Revises: 0005_add_user_is_system
Create Date: 2026-08-14 00:00:00.000000

Редакторы встречи -- пользователи, которые могут редактировать встречу
(добавлять/изменять поля, управлять участниками). Аналог attendees, но
с правами на редактирование, а не только на участие.
"""

from alembic import op
import sqlalchemy as sa

revision = '0006_create_meeting_editors'
down_revision = '0005_add_user_is_system'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'meeting_editors',
        sa.Column('meeting_id', sa.String(36), sa.ForeignKey('meetings.id', ondelete='CASCADE'), primary_key=True, nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True, nullable=False),
    )


def downgrade():
    op.drop_table('meeting_editors')
