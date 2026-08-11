"""
Пакет repositories-слоя. Единственный слой, которому разрешено выполнять
SQLAlchemy-запросы к БД и напрямую работать с ORM-моделями (app.models).

Возвращает только domain-объекты (app.domain.entities), полученные через уже
существующие app.mappers.orm_to_domain -- routes/services дальше не должны видеть ORM напрямую (см. backend/README.md, раздел "ORM / domain /
DTO слои").
"""

from app.repositories.common import new_id, now_iso
from app.repositories.user_repository import UserRepository
from app.repositories.list_repository import ListRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.task_subresource_repository import (
    ChecklistItemRepository,
    CommentRepository,
    NoteRepository,
)
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.recurrence_repository import RecurrenceRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.saved_view_repository import SavedViewRepository

__all__ = [
    "new_id", "now_iso", "UserRepository", "ListRepository", "TaskRepository",
    "ChecklistItemRepository", "NoteRepository", "CommentRepository",
    "MeetingRepository", "RecurrenceRepository", "NotificationRepository", "SavedViewRepository",
]
