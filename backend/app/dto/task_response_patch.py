from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

class CamelModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

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
    meeting_title: Optional[str] = Field(default=None, alias="meetingTitle")
    occurrence_date: Optional[str] = Field(default=None, alias="occurrenceDate")
