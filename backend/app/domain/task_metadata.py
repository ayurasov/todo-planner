from dataclasses import dataclass, field
from typing import Optional

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
    meeting_title: Optional[str] = None
    occurrence_date: Optional[str] = None
