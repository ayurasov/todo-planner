"""
Domain-сущности backend v2 -- простые dataclass'ы без зависимости от
SQLAlchemy/Flask/Pydantic. Прямой аналог `src/domain/entities/factories.js`
на фронтенде: те же имена сущностей и полей (здесь используется snake_case,
как принято в Python; camelCase появляется позже, на уровне DTO/JSON,
см. app/dto и app/mappers).

Смысл слоя: services (следующий шаг, здесь не реализуется) должны работать
только с этими объектами, а не с ORM-моделями напрямую -- это даёт
возможность заменить SQLAlchemy на что угодно без переписывания бизнес-логики.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class User:
    id: str
    name: str
    email: str
    timezone: str = "Europe/Moscow"
    avatar_url: Optional[str] = None
    global_role: str = "user"
    is_active: bool = True
    login: Optional[str] = None
    password_hash: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class TodoList:
    """Имя TodoList (а не List) -- чтобы не конфликтовать со встроенным list."""

    id: str
    title: str
    description: str = ""
    color: str = "#4f7cff"
    is_shared: bool = False
    default_view: str = "list"
    settings: dict = field(default_factory=dict)
    archived: bool = False
    order: int = 0
    owner_ids: list = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class ListMembership:
    id: str
    list_id: str
    user_id: str
    role: str
    added_at: Optional[str] = None


@dataclass
class Task:
    id: str
    title: str
    list_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    description: str = ""
    status: str = "open"
    priority: str = "medium"
    assignee_id: Optional[str] = None
    watcher_ids: list = field(default_factory=list)
    due_date: Optional[str] = None
    start_date: Optional[str] = None
    recurrence_template_id: Optional[str] = None
    tags: list = field(default_factory=list)
    pinned: bool = False
    created_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None
    last_activity_at: Optional[str] = None
    completed_at: Optional[str] = None
    display_standalone: bool = False
    meeting_id: Optional[str] = None
    occurrence_id: Optional[str] = None


@dataclass
class Meeting:
    id: str
    title: str
    date: str
    description: str = ""
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    attendee_ids: list = field(default_factory=list)
    color: str = "#4f7cff"
    archived: bool = False
    order: int = 0
    link: str = ""
    recurrence: Optional[dict] = None
    occurrences: list = field(default_factory=list)
    # Агрегат "не выполнено в серии" -- считается backend'ом в
MeetingRepository.unfinished_total_count, перенесён с фронта (см. backend/README.md).
    unfinished_count: int = 0


@dataclass
class MeetingOccurrence:
    id: str
    meeting_id: str
    date: str
    description: str = ""
    link: str = ""
    generated_at: Optional[str] = None


@dataclass
class ChecklistItem:
    id: str
    task_id: str
    title: str
    done: bool = False
    order: int = 0
    recurrence_scope: str = "instance_only"


@dataclass
class Note:
    id: str
    task_id: str
    content_json: dict = field(default_factory=lambda: {"type": "doc", "content": []})
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None


@dataclass
class Attachment:
    id: str
    file_name: str
    mime_type: str
    url: str
    size: int = 0
    task_id: Optional[str] = None
    note_id: Optional[str] = None
    uploaded_by: Optional[str] = None
    uploaded_at: Optional[str] = None


@dataclass
class RecurrenceTemplate:
    id: str
    list_id: str
    title_template: str
    type: str
    rule: dict = field(default_factory=dict)
    timezone: str = "Europe/Moscow"
    generate_ahead_count: int = 1
    last_generated_instance_date: Optional[str] = None
    checklist_template: list = field(default_factory=list)


@dataclass
class HistoryEntry:
    id: str
    task_id: str
    actor_id: Optional[str]
    type: str
    timestamp: Optional[str] = None
    field: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    comment: Optional[str] = None


@dataclass
class Comment:
    id: str
    task_id: str
    author_id: Optional[str]
    text: str
    created_at: Optional[str] = None
    edited_at: Optional[str] = None
    mentions: list = field(default_factory=list)


@dataclass
class SavedView:
    id: str
    user_id: str
    name: str
    filters: dict = field(default_factory=dict)
    sort: dict = field(default_factory=lambda: {"field": "score", "dir": "desc"})
    group_by: Optional[str] = None
    pinned: bool = False


@dataclass
class Notification:
    id: str
    user_id: str
    type: str
    title: str
    body: str = ""
    task_id: Optional[str] = None
    list_id: Optional[str] = None
    actor_id: Optional[str] = None
    created_at: Optional[str] = None
    read: bool = False


@dataclass
class ReminderTrigger:
    id: str
    task_id: str
    type: str = "time"
    time_offset: Optional[int] = None
    geo: Optional[dict] = None
    is_enabled: bool = True


@dataclass
class CalendarIntegration:
    id: str
    user_id: str
    provider: str = "none"
    status: str = "disconnected"
    sync_settings: dict = field(default_factory=dict)
    last_synced_at: Optional[str] = None
