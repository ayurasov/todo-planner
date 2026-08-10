"""
SQLAlchemy ORM-модели для backend v2. 1:1 соответствуют таблицам из
`backend/migrations/*.up.sql`. Это самый нижний слой (persistence) --
он ничего не знает про domain/dto/mappers и не должен импортироваться
из routes напрямую (см. app/domain и app/mappers).
"""

from app.extensions import db


class UserORM(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Text, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False, unique=True)
    login = db.Column(db.Text, unique=True)
    password_hash = db.Column(db.Text)
    timezone = db.Column(db.Text, nullable=False, default="Europe/Moscow")
    avatar_url = db.Column(db.Text)
    global_role = db.Column(db.Text, nullable=False, default="user")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.Text, nullable=False)


class ListORM(db.Model):
    __tablename__ = "lists"

    id = db.Column(db.Text, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    color = db.Column(db.Text, nullable=False, default="#4f7cff")
    is_shared = db.Column(db.Boolean, nullable=False, default=False)
    default_view = db.Column(db.Text, nullable=False, default="list")
    settings = db.Column(db.Text, nullable=False, default="{}")
    archived = db.Column(db.Boolean, nullable=False, default=False)
    order_index = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.Text, nullable=False)


class ListMembershipORM(db.Model):
    __tablename__ = "list_memberships"

    id = db.Column(db.Text, primary_key=True)
    list_id = db.Column(db.Text, db.ForeignKey("lists.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Text, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = db.Column(db.Text, nullable=False)
    added_at = db.Column(db.Text, nullable=False)


class MeetingORM(db.Model):
    __tablename__ = "meetings"

    id = db.Column(db.Text, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    date = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    link = db.Column(db.Text, nullable=False, default="")
    color = db.Column(db.Text, nullable=False, default="#4f7cff")
    archived = db.Column(db.Boolean, nullable=False, default=False)
    order_index = db.Column(db.Integer, nullable=False, default=0)
    recurrence = db.Column(db.Text)
    created_by = db.Column(db.Text, db.ForeignKey("users.id", ondelete="SET NULL"))
    created_at = db.Column(db.Text, nullable=False)


class MeetingAttendeeORM(db.Model):
    __tablename__ = "meeting_attendees"

    meeting_id = db.Column(db.Text, db.ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True)
    user_id = db.Column(db.Text, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)


class MeetingOccurrenceORM(db.Model):
    __tablename__ = "meeting_occurrences"

    id = db.Column(db.Text, primary_key=True)
    meeting_id = db.Column(db.Text, db.ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    date = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    link = db.Column(db.Text, nullable=False, default="")
    generated_at = db.Column(db.Text, nullable=False)


class RecurrenceTemplateORM(db.Model):
    __tablename__ = "recurrence_templates"

    id = db.Column(db.Text, primary_key=True)
    list_id = db.Column(db.Text, db.ForeignKey("lists.id", ondelete="CASCADE"), nullable=False)
    title_template = db.Column(db.Text, nullable=False)
    type = db.Column(db.Text, nullable=False)
    rule = db.Column(db.Text, nullable=False, default="{}")
    timezone = db.Column(db.Text, nullable=False, default="Europe/Moscow")
    generate_ahead_count = db.Column(db.Integer, nullable=False, default=1)
    last_generated_instance_date = db.Column(db.Text)
    checklist_template = db.Column(db.Text, nullable=False, default="[]")


class TaskORM(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Text, primary_key=True)
    list_id = db.Column(db.Text, db.ForeignKey("lists.id", ondelete="CASCADE"))
    parent_task_id = db.Column(db.Text, db.ForeignKey("tasks.id", ondelete="SET NULL"))
    meeting_id = db.Column(db.Text, db.ForeignKey("meetings.id", ondelete="SET NULL"))
    occurrence_id = db.Column(db.Text, db.ForeignKey("meeting_occurrences.id", ondelete="SET NULL"))
    recurrence_template_id = db.Column(db.Text, db.ForeignKey("recurrence_templates.id", ondelete="SET NULL"))
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    status = db.Column(db.Text, nullable=False, default="open")
    priority = db.Column(db.Text, nullable=False, default="medium")
    assignee_id = db.Column(db.Text, db.ForeignKey("users.id", ondelete="SET NULL"))
    created_by = db.Column(db.Text, db.ForeignKey("users.id", ondelete="SET NULL"))
    updated_by = db.Column(db.Text, db.ForeignKey("users.id", ondelete="SET NULL"))
    due_date = db.Column(db.Text)
    start_date = db.Column(db.Text)
    pinned = db.Column(db.Boolean, nullable=False, default=False)
    display_standalone = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.Text, nullable=False)
    last_activity_at = db.Column(db.Text, nullable=False)
    completed_at = db.Column(db.Text)


class TaskTagORM(db.Model):
    __tablename__ = "task_tags"

    task_id = db.Column(db.Text, db.ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    tag = db.Column(db.Text, primary_key=True)


class TaskWatcherORM(db.Model):
    __tablename__ = "task_watchers"

    task_id = db.Column(db.Text, db.ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    user_id = db.Column(db.Text, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)


class ChecklistItemORM(db.Model):
    __tablename__ = "checklist_items"

    id = db.Column(db.Text, primary_key=True)
    task_id = db.Column(db.Text, db.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.Text, nullable=False)
    done = db.Column(db.Boolean, nullable=False, default=False)
    order_index = db.Column(db.Integer, nullable=False, default=0)
    recurrence_scope = db.Column(db.Text, nullable=False, default="instance_only")


class NoteORM(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Text, primary_key=True)
    task_id = db.Column(db.Text, db.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    content = db.Column(db.Text, nullable=False, default='{"type":"doc","content":[]}')
    updated_by = db.Column(db.Text, db.ForeignKey("users.id", ondelete="SET NULL"))
    created_at = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.Text, nullable=False)


class AttachmentORM(db.Model):
    __tablename__ = "attachments"

    id = db.Column(db.Text, primary_key=True)
    task_id = db.Column(db.Text, db.ForeignKey("tasks.id", ondelete="CASCADE"))
    note_id = db.Column(db.Text, db.ForeignKey("notes.id", ondelete="CASCADE"))
    file_name = db.Column(db.Text, nullable=False)
    mime_type = db.Column(db.Text, nullable=False)
    url = db.Column(db.Text, nullable=False)
    size = db.Column(db.Integer, nullable=False, default=0)
    uploaded_by = db.Column(db.Text, db.ForeignKey("users.id", ondelete="SET NULL"))
    uploaded_at = db.Column(db.Text, nullable=False)


class TaskHistoryEntryORM(db.Model):
    __tablename__ = "task_history_entries"

    id = db.Column(db.Text, primary_key=True)
    task_id = db.Column(db.Text, db.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    actor_id = db.Column(db.Text, db.ForeignKey("users.id", ondelete="SET NULL"))
    timestamp = db.Column(db.Text, nullable=False)
    type = db.Column(db.Text, nullable=False)
    field = db.Column(db.Text)
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    comment = db.Column(db.Text)


class CommentORM(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Text, primary_key=True)
    task_id = db.Column(db.Text, db.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    author_id = db.Column(db.Text, db.ForeignKey("users.id", ondelete="SET NULL"))
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.Text, nullable=False)
    edited_at = db.Column(db.Text)


class CommentMentionORM(db.Model):
    __tablename__ = "comment_mentions"

    comment_id = db.Column(db.Text, db.ForeignKey("comments.id", ondelete="CASCADE"), primary_key=True)
    user_id = db.Column(db.Text, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)


class SavedViewORM(db.Model):
    __tablename__ = "saved_views"

    id = db.Column(db.Text, primary_key=True)
    user_id = db.Column(db.Text, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = db.Column(db.Text, nullable=False)
    filters = db.Column(db.Text, nullable=False, default="{}")
    sort = db.Column(db.Text, nullable=False, default='{"field":"score","dir":"desc"}')
    group_by = db.Column(db.Text)
    pinned = db.Column(db.Boolean, nullable=False, default=False)


class NotificationORM(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Text, primary_key=True)
    user_id = db.Column(db.Text, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = db.Column(db.Text, nullable=False)
    task_id = db.Column(db.Text, db.ForeignKey("tasks.id", ondelete="SET NULL"))
    list_id = db.Column(db.Text, db.ForeignKey("lists.id", ondelete="SET NULL"))
    actor_id = db.Column(db.Text, db.ForeignKey("users.id", ondelete="SET NULL"))
    title = db.Column(db.Text, nullable=False)
    body = db.Column(db.Text, nullable=False, default="")
    read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.Text, nullable=False)


class ReminderTriggerORM(db.Model):
    __tablename__ = "reminder_triggers"

    id = db.Column(db.Text, primary_key=True)
    task_id = db.Column(db.Text, db.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    type = db.Column(db.Text, nullable=False, default="time")
    time_offset = db.Column(db.Integer)
    geo = db.Column(db.Text)
    is_enabled = db.Column(db.Boolean, nullable=False, default=True)


class CalendarIntegrationORM(db.Model):
    __tablename__ = "calendar_integrations"

    id = db.Column(db.Text, primary_key=True)
    user_id = db.Column(db.Text, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    provider = db.Column(db.Text, nullable=False, default="none")
    status = db.Column(db.Text, nullable=False, default="disconnected")
    sync_settings = db.Column(db.Text, nullable=False, default="{}")
    last_synced_at = db.Column(db.Text)
