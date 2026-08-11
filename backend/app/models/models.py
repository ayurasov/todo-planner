"""
SQLAlchemy ORM-модели для backend v2. Соответствуют таблицам из
`backend/migrations/*.up.sql` (использованы как основа для начальной Alembic-ревизии).
Типы колонок выровнены под совместимость с SQLite (dev/test) и PostgreSQL (production):
строковые UUID id, timezone-aware DateTime, JSON/JSONB для структурированных полей.
Это самый нижний слой (persistence) -- он ничего не знает про domain/dto/mappers
и не должен импортироваться из routes напрямую (см. app/domain и app/mappers).
"""

from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON

from app.extensions import db


class TZDateTime(TypeDecorator):
    """DateTime(timezone=True), который также принимает на вход старый
    ISO-8601 UTC формат с 'Z' (как в app.repositories.common.now_iso до рефакторинга),
    чтобы не ломать обратную совместимость с mappers/routes."""

    impl = db.DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, str):
            if value.endswith("Z"):
                value = value[:-1] + "+00:00"
            return __import__("datetime").datetime.fromisoformat(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if getattr(value, "tzinfo", None) is None:
            return value.replace(tzinfo=__import__("datetime").timezone.utc)
        return value


class JSONVariant(TypeDecorator):
    """JSON на SQLite, JSONB на PostgreSQL -- без ручной json.dumps/loads в repositories."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())


ID_LEN = 36


class DepartmentORM(db.Model):
    """Отдел/служба -- плоский справочник (без иерархии, без parent_id),
    настраиваемый администратором. Используется для тегирования пользователей,
    списков задач и встреч (см. department_id в UserORM/ListORM/MeetingORM), а
    также для определения зоны ответственности руководителя (ManagerDepartmentORM).
    """

    __tablename__ = "departments"

    id = db.Column(db.String(ID_LEN), primary_key=True)
    name = db.Column(db.Text, nullable=False, unique=True)
    created_at = db.Column(TZDateTime(), nullable=False)
    updated_at = db.Column(TZDateTime(), nullable=False)


class ManagerDepartmentORM(db.Model):
    """Связь many-to-many "руководитель -- отделы, которыми он управляет".
    Один руководитель (UserORM.global_role == 'manager') может быть назначен
    руководителем нескольких отделов/служб одновременно -- поэтому это
    отдельная таблица связей, а не одиночный department_id на UserORM.
    """

    __tablename__ = "manager_departments"

    user_id = db.Column(db.String(ID_LEN), db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    department_id = db.Column(db.String(ID_LEN), db.ForeignKey("departments.id", ondelete="CASCADE"), primary_key=True)


class UserORM(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(ID_LEN), primary_key=True)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False, unique=True)
    login = db.Column(db.Text, unique=True)
    password_hash = db.Column(db.Text)
    timezone = db.Column(db.Text, nullable=False, default="Europe/Moscow")
    avatar_url = db.Column(db.Text)
    global_role = db.Column(db.Text, nullable=False, default="user")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    position = db.Column(db.Text)
    department = db.Column(db.Text)
    # department_id -- ссылка на настраиваемый справочник Department (плоский
    # список, без иерархии). Отдельно от manager_departments -- это отдел, в
    # котором сам сотрудник работает, а не который он возглавляет.
    department_id = db.Column(db.String(ID_LEN), db.ForeignKey("departments.id", ondelete="SET NULL"))
    created_at = db.Column(TZDateTime(), nullable=False)
    updated_at = db.Column(TZDateTime(), nullable=False)


class ListORM(db.Model):
    __tablename__ = "lists"

    id = db.Column(db.String(ID_LEN), primary_key=True)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    color = db.Column(db.Text, nullable=False, default="#4f7cff")
    is_shared = db.Column(db.Boolean, nullable=False, default=False)
    default_view = db.Column(db.Text, nullable=False, default="list")
    settings = db.Column(JSONVariant(), nullable=False, default=dict)
    archived = db.Column(db.Boolean, nullable=False, default=False)
    order_index = db.Column(db.Integer, nullable=False, default=0)
    department_id = db.Column(db.String(ID_LEN), db.ForeignKey("departments.id", ondelete="SET NULL"))
    created_at = db.Column(TZDateTime(), nullable=False)
    updated_at = db.Column(TZDateTime(), nullable=False)


class ListMembershipORM(db.Model):
    __tablename__ = "list_memberships"

    id = db.Column(db.String(ID_LEN), primary_key=True)
    list_id = db.Column(db.String(ID_LEN), db.ForeignKey("lists.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.String(ID_LEN), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = db.Column(db.Text, nullable=False)
    added_at = db.Column(TZDateTime(), nullable=False)


class MeetingORM(db.Model):
    __tablename__ = "meetings"

    id = db.Column(db.String(ID_LEN), primary_key=True)
    title = db.Column(db.Text, nullable=False)
    date = db.Column(TZDateTime(), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    link = db.Column(db.Text, nullable=False, default="")
    color = db.Column(db.Text, nullable=False, default="#4f7cff")
    archived = db.Column(db.Boolean, nullable=False, default=False)
    order_index = db.Column(db.Integer, nullable=False, default=0)
    recurrence = db.Column(JSONVariant())
    department_id = db.Column(db.String(ID_LEN), db.ForeignKey("departments.id", ondelete="SET NULL"))
    created_by = db.Column(db.String(ID_LEN), db.ForeignKey("users.id", ondelete="SET NULL"))
    created_at = db.Column(TZDateTime(), nullable=False)


class MeetingAttendeeORM(db.Model):
    __tablename__ = "meeting_attendees"

    meeting_id = db.Column(db.String(ID_LEN), db.ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True)
    user_id = db.Column(db.String(ID_LEN), db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)


class MeetingOccurrenceORM(db.Model):
    __tablename__ = "meeting_occurrences"

    id = db.Column(db.String(ID_LEN), primary_key=True)
    meeting_id = db.Column(db.String(ID_LEN), db.ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    date = db.Column(TZDateTime(), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    link = db.Column(db.Text, nullable=False, default="")
    generated_at = db.Column(TZDateTime(), nullable=False)


class RecurrenceTemplateORM(db.Model):
    __tablename__ = "recurrence_templates"

    id = db.Column(db.String(ID_LEN), primary_key=True)
    list_id = db.Column(db.String(ID_LEN), db.ForeignKey("lists.id", ondelete="CASCADE"), nullable=False)
    title_template = db.Column(db.Text, nullable=False)
    type = db.Column(db.Text, nullable=False)
    rule = db.Column(JSONVariant(), nullable=False, default=dict)
    timezone = db.Column(db.Text, nullable=False, default="Europe/Moscow")
    generate_ahead_count = db.Column(db.Integer, nullable=False, default=1)
    last_generated_instance_date = db.Column(TZDateTime())
    checklist_template = db.Column(JSONVariant(), nullable=False, default=list)


class TaskORM(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.String(ID_LEN), primary_key=True)
    list_id = db.Column(db.String(ID_LEN), db.ForeignKey("lists.id", ondelete="CASCADE"))
    parent_task_id = db.Column(db.String(ID_LEN), db.ForeignKey("tasks.id", ondelete="SET NULL"))
    meeting_id = db.Column(db.String(ID_LEN), db.ForeignKey("meetings.id", ondelete="SET NULL"))
    occurrence_id = db.Column(db.String(ID_LEN), db.ForeignKey("meeting_occurrences.id", ondelete="SET NULL"))
    recurrence_template_id = db.Column(db.String(ID_LEN), db.ForeignKey("recurrence_templates.id", ondelete="SET NULL"))
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    status = db.Column(db.Text, nullable=False, default="open")
    priority = db.Column(db.Text, nullable=False, default="medium")
    assignee_id = db.Column(db.String(ID_LEN), db.ForeignKey("users.id", ondelete="SET NULL"))
    created_by = db.Column(db.String(ID_LEN), db.ForeignKey("users.id", ondelete="SET NULL"))
    updated_by = db.Column(db.String(ID_LEN), db.ForeignKey("users.id", ondelete="SET NULL"))
    due_date = db.Column(TZDateTime())
    start_date = db.Column(TZDateTime())
    pinned = db.Column(db.Boolean, nullable=False, default=False)
    display_standalone = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(TZDateTime(), nullable=False)
    updated_at = db.Column(TZDateTime(), nullable=False)
    last_activity_at = db.Column(TZDateTime(), nullable=False)
    completed_at = db.Column(TZDateTime())


class TaskTagORM(db.Model):
    __tablename__ = "task_tags"

    task_id = db.Column(db.String(ID_LEN), db.ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    tag = db.Column(db.Text, primary_key=True)


class TaskWatcherORM(db.Model):
    __tablename__ = "task_watchers"

    task_id = db.Column(db.String(ID_LEN), db.ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    user_id = db.Column(db.String(ID_LEN), db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)


class ChecklistItemORM(db.Model):
    __tablename__ = "checklist_items"

    id = db.Column(db.String(ID_LEN), primary_key=True)
    task_id = db.Column(db.String(ID_LEN), db.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.Text, nullable=False)
    done = db.Column(db.Boolean, nullable=False, default=False)
    order_index = db.Column(db.Integer, nullable=False, default=0)
    recurrence_scope = db.Column(db.Text, nullable=False, default="instance_only")


class NoteORM(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.String(ID_LEN), primary_key=True)
    task_id = db.Column(db.String(ID_LEN), db.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    content = db.Column(JSONVariant(), nullable=False, default=lambda: {"type": "doc", "content": []})
    updated_by = db.Column(db.String(ID_LEN), db.ForeignKey("users.id", ondelete="SET NULL"))
    created_at = db.Column(TZDateTime(), nullable=False)
    updated_at = db.Column(TZDateTime(), nullable=False)


class AttachmentORM(db.Model):
    __tablename__ = "attachments"

    id = db.Column(db.String(ID_LEN), primary_key=True)
    task_id = db.Column(db.String(ID_LEN), db.ForeignKey("tasks.id", ondelete="CASCADE"))
    note_id = db.Column(db.String(ID_LEN), db.ForeignKey("notes.id", ondelete="CASCADE"))
    file_name = db.Column(db.Text, nullable=False)
    mime_type = db.Column(db.Text, nullable=False)
    url = db.Column(db.Text, nullable=False)
    size = db.Column(db.Integer, nullable=False, default=0)
    uploaded_by = db.Column(db.String(ID_LEN), db.ForeignKey("users.id", ondelete="SET NULL"))
    uploaded_at = db.Column(TZDateTime(), nullable=False)


class TaskHistoryEntryORM(db.Model):
    __tablename__ = "task_history_entries"

    id = db.Column(db.String(ID_LEN), primary_key=True)
    task_id = db.Column(db.String(ID_LEN), db.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    actor_id = db.Column(db.String(ID_LEN), db.ForeignKey("users.id", ondelete="SET NULL"))
    timestamp = db.Column(TZDateTime(), nullable=False)
    type = db.Column(db.Text, nullable=False)
    field = db.Column(db.Text)
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    comment = db.Column(db.Text)


class CommentORM(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.String(ID_LEN), primary_key=True)
    task_id = db.Column(db.String(ID_LEN), db.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    author_id = db.Column(db.String(ID_LEN), db.ForeignKey("users.id", ondelete="SET NULL"))
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(TZDateTime(), nullable=False)
    edited_at = db.Column(TZDateTime())


class CommentMentionORM(db.Model):
    __tablename__ = "comment_mentions"

    comment_id = db.Column(db.String(ID_LEN), db.ForeignKey("comments.id", ondelete="CASCADE"), primary_key=True)
    user_id = db.Column(db.String(ID_LEN), db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)


class SavedViewORM(db.Model):
    __tablename__ = "saved_views"

    id = db.Column(db.String(ID_LEN), primary_key=True)
    user_id = db.Column(db.String(ID_LEN), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = db.Column(db.Text, nullable=False)
    filters = db.Column(JSONVariant(), nullable=False, default=dict)
    sort = db.Column(JSONVariant(), nullable=False, default=lambda: {"field": "score", "dir": "desc"})
    group_by = db.Column(db.Text)
    pinned = db.Column(db.Boolean, nullable=False, default=False)


class NotificationORM(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.String(ID_LEN), primary_key=True)
    user_id = db.Column(db.String(ID_LEN), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = db.Column(db.Text, nullable=False)
    task_id = db.Column(db.String(ID_LEN), db.ForeignKey("tasks.id", ondelete="SET NULL"))
    list_id = db.Column(db.String(ID_LEN), db.ForeignKey("lists.id", ondelete="SET NULL"))
    actor_id = db.Column(db.String(ID_LEN), db.ForeignKey("users.id", ondelete="SET NULL"))
    title = db.Column(db.Text, nullable=False)
    body = db.Column(db.Text, nullable=False, default="")
    read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(TZDateTime(), nullable=False)


class ReminderTriggerORM(db.Model):
    __tablename__ = "reminder_triggers"

    id = db.Column(db.String(ID_LEN), primary_key=True)
    task_id = db.Column(db.String(ID_LEN), db.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    type = db.Column(db.Text, nullable=False, default="time")
    time_offset = db.Column(db.Integer)
    geo = db.Column(JSONVariant())
    is_enabled = db.Column(db.Boolean, nullable=False, default=True)


class CalendarIntegrationORM(db.Model):
    __tablename__ = "calendar_integrations"

    id = db.Column(db.String(ID_LEN), primary_key=True)
    user_id = db.Column(db.String(ID_LEN), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    provider = db.Column(db.Text, nullable=False, default="none")
    status = db.Column(db.Text, nullable=False, default="disconnected")
    sync_settings = db.Column(JSONVariant(), nullable=False, default=dict)
    last_synced_at = db.Column(TZDateTime())
