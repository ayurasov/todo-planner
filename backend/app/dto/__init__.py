"""
Пакет DTO-слоя. Реэкспортирует все Pydantic-схемы из `schemas.py`, чтобы
можно было писать `from app.dto import TaskCreateDTO` и т.п.
"""

from app.dto.schemas import (
    CamelModel,
    UserResponseDTO,
    LoginRequestDTO,
    LoginResponseDTO,
    ChangePasswordRequestDTO,
    ListResponseDTO,
    ListCreateDTO,
    ListUpdateDTO,
    ListMembershipResponseDTO,
    ChecklistItemResponseDTO,
    ChecklistItemCreateDTO,
    CommentResponseDTO,
    CommentCreateDTO,
    NoteResponseDTO,
    NoteUpdateDTO,
    AttachmentResponseDTO,
    HistoryEntryResponseDTO,
    TaskResponseDTO,
    TaskCreateDTO,
    TaskUpdateDTO,
    MeetingOccurrenceResponseDTO,
    MeetingResponseDTO,
    MeetingCreateDTO,
    MeetingUpdateDTO,
    RecurrenceTemplateResponseDTO,
    RecurrenceTemplateCreateDTO,
    RecurrenceTemplateUpdateDTO,
    SavedViewResponseDTO,
    SavedViewCreateDTO,
    SavedViewUpdateDTO,
    NotificationResponseDTO,
    NotificationCreateDTO,
    NotificationUpdateDTO,
)

__all__ = [
    "CamelModel", "UserResponseDTO", "LoginRequestDTO", "LoginResponseDTO",
    "ChangePasswordRequestDTO",
    "ListResponseDTO", "ListCreateDTO", "ListUpdateDTO", "ListMembershipResponseDTO",
    "ChecklistItemResponseDTO", "ChecklistItemCreateDTO", "CommentResponseDTO",
    "CommentCreateDTO", "NoteResponseDTO", "NoteUpdateDTO", "AttachmentResponseDTO",
    "HistoryEntryResponseDTO", "TaskResponseDTO", "TaskCreateDTO", "TaskUpdateDTO",
    "MeetingOccurrenceResponseDTO", "MeetingResponseDTO", "MeetingCreateDTO",
    "MeetingUpdateDTO", "RecurrenceTemplateResponseDTO", "RecurrenceTemplateCreateDTO",
    "RecurrenceTemplateUpdateDTO", "SavedViewResponseDTO", "SavedViewCreateDTO",
    "SavedViewUpdateDTO", "NotificationResponseDTO", "NotificationCreateDTO",
    "NotificationUpdateDTO",
]
