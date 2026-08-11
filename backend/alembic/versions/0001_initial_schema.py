"""Initial schema ported from legacy SQL files in backend/migrations

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-08-11 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def _json_type():
    return postgresql.JSONB(astext_type=sa.Text())


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('email', sa.Text(), nullable=False, unique=True),
        sa.Column('login', sa.Text(), nullable=True, unique=True),
        sa.Column('password_hash', sa.Text(), nullable=True),
        sa.Column('timezone', sa.Text(), nullable=False, server_default='Europe/Moscow'),
        sa.Column('avatar_url', sa.Text(), nullable=True),
        sa.Column('global_role', sa.Text(), nullable=False, server_default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("global_role IN ('admin', 'user')", name='ck_users_global_role'),
    )
    op.create_table(
        'lists',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('color', sa.Text(), nullable=False, server_default='#4f7cff'),
        sa.Column('is_shared', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('default_view', sa.Text(), nullable=False, server_default='list'),
        sa.Column('settings', _json_type(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('archived', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        'list_memberships',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('list_id', sa.String(length=36), sa.ForeignKey('lists.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.Text(), nullable=False),
        sa.Column('added_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role IN ('owner', 'editor', 'viewer', 'assignee')", name='ck_list_memberships_role'),
    )
    op.create_index('idx_list_memberships_list_user', 'list_memberships', ['list_id', 'user_id'], unique=True)
    op.create_table(
        'meetings',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('link', sa.Text(), nullable=False, server_default=''),
        sa.Column('color', sa.Text(), nullable=False, server_default='#4f7cff'),
        sa.Column('archived', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('recurrence', _json_type(), nullable=True),
        sa.Column('created_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        'meeting_attendees',
        sa.Column('meeting_id', sa.String(length=36), sa.ForeignKey('meetings.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    )
    op.create_table(
        'meeting_occurrences',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('meeting_id', sa.String(length=36), sa.ForeignKey('meetings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('link', sa.Text(), nullable=False, server_default=''),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('idx_meeting_occurrences_meeting_id', 'meeting_occurrences', ['meeting_id'])
    op.create_table(
        'recurrence_templates',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('list_id', sa.String(length=36), sa.ForeignKey('lists.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title_template', sa.Text(), nullable=False),
        sa.Column('type', sa.Text(), nullable=False),
        sa.Column('rule', _json_type(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('timezone', sa.Text(), nullable=False, server_default='Europe/Moscow'),
        sa.Column('generate_ahead_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('last_generated_instance_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('checklist_template', _json_type(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.CheckConstraint("type IN ('fixed_schedule', 'completion_based')", name='ck_recurrence_templates_type'),
    )
    op.create_table(
        'tasks',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('list_id', sa.String(length=36), sa.ForeignKey('lists.id', ondelete='CASCADE')),
        sa.Column('parent_task_id', sa.String(length=36), sa.ForeignKey('tasks.id', ondelete='SET NULL')),
        sa.Column('meeting_id', sa.String(length=36), sa.ForeignKey('meetings.id', ondelete='SET NULL')),
        sa.Column('occurrence_id', sa.String(length=36), sa.ForeignKey('meeting_occurrences.id', ondelete='SET NULL')),
        sa.Column('recurrence_template_id', sa.String(length=36), sa.ForeignKey('recurrence_templates.id', ondelete='SET NULL')),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('status', sa.Text(), nullable=False, server_default='open'),
        sa.Column('priority', sa.Text(), nullable=False, server_default='medium'),
        sa.Column('assignee_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('created_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('updated_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('pinned', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('display_standalone', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('open', 'in_progress', 'done', 'cancelled')", name='ck_tasks_status'),
        sa.CheckConstraint("priority IN ('low', 'medium', 'high', 'urgent')", name='ck_tasks_priority'),
    )
    op.create_index('idx_tasks_list_id', 'tasks', ['list_id'])
    op.create_index('idx_tasks_assignee_id', 'tasks', ['assignee_id'])
    op.create_index('idx_tasks_status', 'tasks', ['status'])
    op.create_index('idx_tasks_due_date', 'tasks', ['due_date'])
    op.create_index('idx_tasks_created_at', 'tasks', ['created_at'])
    op.create_index('idx_tasks_completed_at', 'tasks', ['completed_at'])
    op.create_index('idx_tasks_meeting_id', 'tasks', ['meeting_id'])
    op.create_table(
        'task_tags',
        sa.Column('task_id', sa.String(length=36), sa.ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('tag', sa.Text(), primary_key=True),
    )
    op.create_index('idx_task_tags_tag', 'task_tags', ['tag'])
    op.create_table(
        'task_watchers',
        sa.Column('task_id', sa.String(length=36), sa.ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    )
    op.create_table(
        'checklist_items',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('task_id', sa.String(length=36), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('done', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('recurrence_scope', sa.Text(), nullable=False, server_default='instance_only'),
        sa.CheckConstraint("recurrence_scope IN ('instance_only', 'series_default')", name='ck_checklist_items_recurrence_scope'),
    )
    op.create_index('idx_checklist_items_task_id', 'checklist_items', ['task_id'])
    op.create_table(
        'notes',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('task_id', sa.String(length=36), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content', _json_type(), nullable=False, server_default=sa.text("'{\"type\":\"doc\",\"content\":[]}'::jsonb")),
        sa.Column('updated_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('idx_notes_task_id', 'notes', ['task_id'])
    op.create_table(
        'attachments',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('task_id', sa.String(length=36), sa.ForeignKey('tasks.id', ondelete='CASCADE')),
        sa.Column('note_id', sa.String(length=36), sa.ForeignKey('notes.id', ondelete='CASCADE')),
        sa.Column('file_name', sa.Text(), nullable=False),
        sa.Column('mime_type', sa.Text(), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('size', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('uploaded_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('idx_attachments_task_id', 'attachments', ['task_id'])
    op.create_index('idx_attachments_note_id', 'attachments', ['note_id'])
    op.create_table(
        'task_history_entries',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('task_id', sa.String(length=36), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('actor_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('type', sa.Text(), nullable=False),
        sa.Column('field', sa.Text(), nullable=True),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
    )
    op.create_index('idx_task_history_task_id_timestamp', 'task_history_entries', ['task_id', 'timestamp'])
    op.create_table(
        'comments',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('task_id', sa.String(length=36), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('author_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('edited_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_comments_task_id', 'comments', ['task_id'])
    op.create_table(
        'comment_mentions',
        sa.Column('comment_id', sa.String(length=36), sa.ForeignKey('comments.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    )
    op.create_table(
        'saved_views',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('filters', _json_type(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('sort', _json_type(), nullable=False, server_default=sa.text("'{\"field\":\"score\",\"dir\":\"desc\"}'::jsonb")),
        sa.Column('group_by', sa.Text(), nullable=True),
        sa.Column('pinned', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index('idx_saved_views_user_id', 'saved_views', ['user_id'])
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.Text(), nullable=False),
        sa.Column('task_id', sa.String(length=36), sa.ForeignKey('tasks.id', ondelete='SET NULL')),
        sa.Column('list_id', sa.String(length=36), sa.ForeignKey('lists.id', ondelete='SET NULL')),
        sa.Column('actor_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False, server_default=''),
        sa.Column('read', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("type IN ('due_soon', 'overdue', 'mention', 'task_assigned', 'task_changed', 'meeting_changed')", name='ck_notifications_type'),
    )
    op.create_index('idx_notifications_user_id', 'notifications', ['user_id'])
    op.create_table(
        'reminder_triggers',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('task_id', sa.String(length=36), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.Text(), nullable=False, server_default='time'),
        sa.Column('time_offset', sa.Integer(), nullable=True),
        sa.Column('geo', _json_type(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.CheckConstraint("type IN ('time', 'location')", name='ck_reminder_triggers_type'),
    )
    op.create_index('idx_reminder_triggers_task_id', 'reminder_triggers', ['task_id'])
    op.create_table(
        'calendar_integrations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('provider', sa.Text(), nullable=False, server_default='none'),
        sa.Column('status', sa.Text(), nullable=False, server_default='disconnected'),
        sa.Column('sync_settings', _json_type(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("provider IN ('none', 'exchange', 'google')", name='ck_calendar_integrations_provider'),
        sa.CheckConstraint("status IN ('disconnected', 'connected', 'error')", name='ck_calendar_integrations_status'),
    )


def downgrade():
    op.drop_table('calendar_integrations')
    op.drop_index('idx_reminder_triggers_task_id', table_name='reminder_triggers')
    op.drop_table('reminder_triggers')
    op.drop_index('idx_notifications_user_id', table_name='notifications')
    op.drop_table('notifications')
    op.drop_index('idx_saved_views_user_id', table_name='saved_views')
    op.drop_table('saved_views')
    op.drop_table('comment_mentions')
    op.drop_index('idx_comments_task_id', table_name='comments')
    op.drop_table('comments')
    op.drop_index('idx_task_history_task_id_timestamp', table_name='task_history_entries')
    op.drop_table('task_history_entries')
    op.drop_index('idx_attachments_note_id', table_name='attachments')
    op.drop_index('idx_attachments_task_id', table_name='attachments')
    op.drop_table('attachments')
    op.drop_index('idx_notes_task_id', table_name='notes')
    op.drop_table('notes')
    op.drop_index('idx_checklist_items_task_id', table_name='checklist_items')
    op.drop_table('checklist_items')
    op.drop_table('task_watchers')
    op.drop_index('idx_task_tags_tag', table_name='task_tags')
    op.drop_table('task_tags')
    op.drop_index('idx_tasks_meeting_id', table_name='tasks')
    op.drop_index('idx_tasks_completed_at', table_name='tasks')
    op.drop_index('idx_tasks_created_at', table_name='tasks')
    op.drop_index('idx_tasks_due_date', table_name='tasks')
    op.drop_index('idx_tasks_status', table_name='tasks')
    op.drop_index('idx_tasks_assignee_id', table_name='tasks')
    op.drop_index('idx_tasks_list_id', table_name='tasks')
    op.drop_table('tasks')
    op.drop_table('recurrence_templates')
    op.drop_index('idx_meeting_occurrences_meeting_id', table_name='meeting_occurrences')
    op.drop_table('meeting_occurrences')
    op.drop_table('meeting_attendees')
    op.drop_table('meetings')
    op.drop_index('idx_list_memberships_list_user', table_name='list_memberships')
    op.drop_table('list_memberships')
    op.drop_table('lists')
    op.drop_table('users')
