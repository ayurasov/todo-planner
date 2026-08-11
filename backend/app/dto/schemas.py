"""
Pydantic DTO -- request/response-схемы HTTP-слоя backend v2.

Поля здесь в camelCase (через `alias`), чтобы 1:1 совпадать с тем, что уже
ожидает/отдаёт frontend apiClient и mock-репозитории
(см. src/repositories/http/apiClient.js, src/domain/entities/factories.js).
`populate_by_name=True` позволяет создавать DTO как из camelCase JSON
(входящие запросы), так и из python-объектов по snake_case-именам (мапперы).

здесь нет бизнес-логики и нет импортов SQLAlchemy -- только форма данных.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class CamelModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


# --- Users / Auth ---

class UserResponseDTO(CamelModel):
    id: str
    name: str
    email: str
    timezone: str = "Europe/Moscow"
    avatar_url: Optional[str] = Field(default=None, alias="avatarUrl")
    global_role: str = Field(default="user", alias="globalRole")
    is_active: bool = Field(default=True, alias="isActive")
    position: Optional[str] = None
    department: Optional[str] = None


class LoginRequestDTO(CamelModel):
    login: str
    password: str


class LoginResponseDTO(CamelModel):
    user: UserResponseDTO


class ChangePasswordRequestDTO(CamelModel):
    """POST /api/auth/change-password -- смена пароля залогиненным пользователем.
    `current_password` обязателен, чтобы захват чужой активной сессии (XSS/CSRF
    через браузер жертвы) не мог молциа сменить пароль без знания текущего.
    """

    current_password: str = Field(alias="currentPassword")
    new_password: str = Field(alias="newPassword", min_length=8)


# --- Lists ---

class ListResponseDTO(CamelModel):
    id: str
    title: str
    description: str = ""
    color: str = "#4f7cff"
    owner_ids: List[str] = Field(default_factory=list, alias="ownerIds")
    is_shared: bool = Field(default=False, alias="isShared")
    default_view: str = Field(default="list", alias="defaultView")
    created_at: Optional[str] = Field(default=None, alias="createdAt")
    settings: Dict[str, Any] = Field(default_factory=dict)
    archived: bool = False
    order: int = 0


class ListCreateDTO(CamelModel):
    title: str
    description: str = ""
    color: str = "#4f7cff"
    is_shared: bool = Field(default=False, alias="isShared")
    default_view: str = Field(default="list", alias="defaultView")
    settings: Dict[str, Any] = Field(default_factory=dict)


class ListUpdateDTO(CamelModel):
    title: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    is_shared: Optional[bool] = Field(default=None, alias="isShared")
    default_view: Optional[str] = Field(default=None, alias="defaultView")
    settings: Optional[Dict[str, Any]] = None
    archived: Optional[bool] = None
    order: Optional[int] = None


class ListMembershipResponseDTO(CamelModel):
    id: str
    list_id: str = Field(alias="listId")
    user_id: str = Field(alias="userId")
    role: str
    added_at: Optional[str] = Field(default=None, alias="addedAt")


# --- Tasks ---

class ChecklistItemResponseDTO(CamelModel):
    id: str
    task_id: str = Field(alias="taskId")
    title: str
    done: bool = False
    order: int = 0
    recurrence_scope: str = Field(default="instance_only", alias="recurrenceScope")


class ChecklistItemCreateDTO(CamelModel):
    title: str
    done: bool = False
    order: int = 0
    recurrence_scope: str = Field(default="instance_only", alias="recurrenceScope")


class CommentResponseDTO(CamelModel):
    id: str
    task_id: str = Field(alias="taskId")
    author_id: Optional[str] = Field(default=None, alias="authorId")
    text: str
    created_at: Optional[str] = Field(default=None, alias="createdAt")
    edited_at: Optional[str] = Field(default=None, alias="editedAt")
    mentions: List[str] = Field(default_factory=list)


class CommentCreateDTO(CamelModel):
    text: str
    mentions: List[str] = Field(default_factory=list)


class NoteResponseDTO(CamelModel):
    id: str
    task_id: str = Field(alias="taskId")
    content_json: Dict[str, Any] = Field(default_factory=lambda: {"type": "doc", "content": []}, alias="contentJSON")
    created_at: Optional[str] = Field(default=None, alias="createdAt")
    updated_at: Optional[str] = Field(default=None, alias="updatedAt")
    updated_by: Optional[str] = Field(default=None, alias="updatedBy")


class NoteUpdateDTO(CamelModel):
    content_json: Dict[str, Any] = Field(alias="contentJSON")


class AttachmentResponseDTO(CamelModel):
    id: str
    task_id: Optional[str] = Field(default=None, alias="taskId")
    note_id: Optional[str] = Field(default=None, alias="noteId")
    file_name: str = Field(alias="fileName")
    mime_type: str = Field(alias="mimeType")
    url: str
    size: int = 0
    uploaded_by: Optional[str] = Field(default=None, alias="uploadedBy")
    uploaded_at: Optional[str] = Field(default=None, alias="uploadedAt")


class HistoryEntryResponseDTO(CamelModel):
    id: str
    task_id: str = Field(alias="taskId")
    actor_id: Optional[str] = Field(default=None, alias="actorId")
    timestamp: Optional[str] = None
    type: str
    field: Optional[str] = None
    old_value: Optional[str] = Field(default=None, alias="oldValue")
    new_value: Optional[str] = Field(default=None, alias="newValue")
    comment: Optional[str] = None


class TaskResponseDTO(CamelModel):
    id: str
    list_id: Optional[str] = Field(default=None, alias="listId")
    parent_task_id: Optional[str] = Field(default=None, alias="parentTaskId")
    title: str
    description: str = ""
    status: str = "open"
    priority: str = "medium"
    assignee_id: Optional[str] = Field(default=None, alias="assigneeId")
    watcher_ids: List[str] = Field(default_factory=list, alias="watcherIds")
    due_date: Optional[str] = Field(default=None, alias="dueDate")
    start_date: Optional[str] = Field(default=None, alias="startDate")
    recurrence_template_id: Optional[str] = Field(default=None, alias="recurrenceTemplateId")
    tags: List[str] = Field(default_factory=list)
    pinned: bool = False
    created_at: Optional[str] = Field(default=None, alias="createdAt")
    created_by: Optional[str] = Field(default=None, alias="createdBy")
    updated_at: Optional[str] = Field(default=None, alias="updatedAt")
    updated_by: Optional[str] = Field(default=None, alias="updatedBy")
    last_activity_at: Optional[str] = Field(default=None, alias="lastActivityAt")
    completed_at: Optional[str] = Field(default=None, alias="completedAt")
    display_standalone: bool = Field(default=False, alias="displayStandalone")
    meeting_id: Optional[str] = Field(default=None, alias="meetingId")
    occurrence_id: Optional[str] = Field(default=None, alias="occurrenceId")


class TaskCreateDTO(CamelModel):
    list_id: Optional[str] = Field(default=None, alias="listId")
    parent_task_id: Optional[str] = Field(default=None, alias="parentTaskId")
    title: str
    description: str = ""
    status: str = "open"
    priority: str = "medium"
    assignee_id: Optional[str] = Field(default=None, alias="assigneeId")
    watcher_ids: List[str] = Field(default_factory=list, alias="watcherIds")
    due_date: Optional[str] = Field(default=None, alias="dueDate")
    start_date: Optional[str] = Field(default=None, alias="startDate")
    recurrence_template_id: Optional[str] = Field(default=None, alias="recurrenceTemplateId")
    tags: List[str] = Field(default_factory=list)
    pinned: bool = False
    meeting_id: Optional[str] = Field(default=None, alias="meetingId")
    occurrence_id: Optional[str] = Field(default=None, alias="occurrenceId")


class TaskUpdateDTO(CamelModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[str] = Field(default=None, alias="assigneeId")
    watcher_ids: Optional[List[str]] = Field(default=None, alias="watcherIds")
    due_date: Optional[str] = Field(default=None, alias="dueDate")
    start_date: Optional[str] = Field(default=None, alias="startDate")
    tags: Optional[List[str]] = None
    pinned: Optional[bool] = None
    display_standalone: Optional[bool] = Field(default=None, alias="displayStandalone")
    completed_at: Optional[str] = Field(default=None, alias="completedAt")


# --- Meetings ---

class MeetingOccurrenceResponseDTO(CamelModel):
    id: str
    meeting_id: str = Field(alias="meetingId")
    date: str
    description: str = ""
    link: str = ""
    generated_at: Optional[str] = Field(default=None, alias="generatedAt")


class MeetingResponseDTO(CamelModel):
    id: str
    title: str
    date: str
    description: str = ""
    created_by: Optional[str] = Field(default=None, alias="createdBy")
    created_at: Optional[str] = Field(default=None, alias="createdAt")
    attendee_ids: List[str] = Field(default_factory=list, alias="attendeeIds")
    color: str = "#4f7cff"
    archived: bool = False
    order: int = 0
    link: str = ""
    recurrence: Optional[Dict[str, Any]] = None
    occurrences: List[MeetingOccurrenceResponseDTO] = Field(default_factory=list)
    # Готовая агрегация "не выполнено в серии" -- перенесено с фронта
    # (MeetingDetailView.vue unfinishedTotalCount) на backend, считается на
    # MeetingRepository.unfinished_total_count и отдаётся всегда готовым полем
    # (см. backend/README.md).
    unfinished_count: int = Field(default=0, alias="unfinishedCount")


class MeetingCreateDTO(CamelModel):
    title: str
    date: str
    description: str = ""
    attendee_ids: List[str] = Field(default_factory=list, alias="attendeeIds")
    color: str = "#4f7cff"
    link: str = ""
    recurrence: Optional[Dict[str, Any]] = None


class MeetingUpdateDTO(CamelModel):
    title: Optional[str] = None
    date: Optional[str] = None
    description: Optional[str] = None
    attendee_ids: Optional[List[str]] = Field(default=None, alias="attendeeIds")
    color: Optional[str] = None
    link: Optional[str] = None
    recurrence: Optional[Dict[str, Any]] = None
    archived: Optional[bool] = None
    order: Optional[int] = None
    occurrences: Optional[List[Dict[str, Any]]] = None


# --- Recurrence templates ---

class RecurrenceTemplateResponseDTO(CamelModel):
    id: str
    list_id: str = Field(alias="listId")
    title_template: str = Field(alias="titleTemplate")
    type: str
    rule: Dict[str, Any] = Field(default_factory=dict)
    timezone: str = "Europe/Moscow"
    generate_ahead_count: int = Field(default=1, alias="generateAheadCount")
    last_generated_instance_date: Optional[str] = Field(default=None, alias="lastGeneratedInstanceDate")
    checklist_template: List[Dict[str, Any]] = Field(default_factory=list, alias="checklistTemplate")


class RecurrenceTemplateCreateDTO(CamelModel):
    list_id: str = Field(alias="listId")
    title_template: str = Field(alias="titleTemplate")
    type: str
    rule: Dict[str, Any] = Field(default_factory=dict)
    timezone: str = "Europe/Moscow"
    generate_ahead_count: int = Field(default=1, alias="generateAheadCount")
    checklist_template: List[Dict[str, Any]] = Field(default_factory=list, alias="checklistTemplate")


class RecurrenceTemplateUpdateDTO(CamelModel):
    title_template: Optional[str] = Field(default=None, alias="titleTemplate")
    rule: Optional[Dict[str, Any]] = None
    timezone: Optional[str] = None
    generate_ahead_count: Optional[int] = Field(default=None, alias="generateAheadCount")
    checklist_template: Optional[List[Dict[str, Any]]] = Field(default=None, alias="checklistTemplate")


# --- Saved views ---

class SavedViewResponseDTO(CamelModel):
    id: str
    user_id: str = Field(alias="userId")
    name: str
    filters: Dict[str, Any] = Field(default_factory=dict)
    sort: Dict[str, Any] = Field(default_factory=lambda: {"field": "score", "dir": "desc"})
    group_by: Optional[str] = Field(default=None, alias="groupBy")
    pinned: bool = False


class SavedViewCreateDTO(CamelModel):
    name: str
    filters: Dict[str, Any] = Field(default_factory=dict)
    sort: Dict[str, Any] = Field(default_factory=lambda: {"field": "score", "dir": "desc"})
    group_by: Optional[str] = Field(default=None, alias="groupBy")
    pinned: bool = False


class SavedViewUpdateDTO(CamelModel):
    name: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    sort: Optional[Dict[str, Any]] = None
    group_by: Optional[str] = Field(default=None, alias="groupBy")
    pinned: Optional[bool] = None


# --- Notifications ---

class NotificationResponseDTO(CamelModel):
    id: str
    user_id: str = Field(alias="userId")
    type: str
    title: str
    body: str = ""
    task_id: Optional[str] = Field(default=None, alias="taskId")
    list_id: Optional[str] = Field(default=None, alias="listId")
    actor_id: Optional[str] = Field(default=None, alias="actorId")
    created_at: Optional[str] = Field(default=None, alias="createdAt")
    read: bool = False


class NotificationCreateDTO(CamelModel):
    type: str
    title: str
    body: str = ""
    task_id: Optional[str] = Field(default=None, alias="taskId")
    list_id: Optional[str] = Field(default=None, alias="listId")
    actor_id: Optional[str] = Field(default=None, alias="actorId")
    user_id: Optional[str] = Field(default=None, alias="userId")


class NotificationUpdateDTO(CamelModel):
    read: Optional[bool] = None
