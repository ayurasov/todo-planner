"""
TaskRepository -- слой доступа к данным для ресурса `tasks`. Содержит
только SQLAlchemy-запросы, возвращает domain-объекты через
`app.mappers.orm_to_domain`. Фильтрация видимых задач делается на сервере.
"""

from app.extensions import db
from app.mappers import orm_to_domain
from app.models import MeetingOccurrenceORM, MeetingORM, TaskORM, TaskTagORM, TaskWatcherORM
from app.repositories.common import new_id, now_iso
from app.services.permission_service import permission_service


class TaskRepository:
    def _watcher_ids(self, task_id: str):
        rows = TaskWatcherORM.query.filter_by(task_id=task_id).all()
        return [row.user_id for row in rows]

    def _tags(self, task_id: str):
        rows = TaskTagORM.query.filter_by(task_id=task_id).all()
        return [row.tag for row in rows]

    def _to_domain(self, row: TaskORM):
        task = orm_to_domain.task(row, watcher_ids=self._watcher_ids(row.id), tags=self._tags(row.id))
        # These are task metadata, not an authorization grant. They let an
        # assignee render the task without exposing the meeting resource.
        meeting = MeetingORM.query.get(row.meeting_id) if row.meeting_id else None
        occurrence = MeetingOccurrenceORM.query.get(row.occurrence_id) if row.occurrence_id else None
        task.meeting_title = meeting.title if meeting else None
        task.occurrence_date = (
            occurrence.date.isoformat() if occurrence and occurrence.date else None
        )
        return task

    def get_by_id(self, task_id: str):
        row = TaskORM.query.get(task_id)
        return self._to_domain(row) if row else None

    def get_visible_for_user(self, user_id: str, *, list_id=None, assignee_id=None,
                              statuses=None, parent_task_id=None, tags=None):
        """Return tasks visible to the current user.

        An assignee can see their assigned task even when they are not an
        attendee of the related meeting. Meeting ACLs themselves are unchanged.
        """
        is_admin = permission_service.is_global_admin(user_id)
        query = TaskORM.query
        if list_id is not None:
            query = query.filter(TaskORM.list_id == list_id)
        if assignee_id is not None:
            query = query.filter(TaskORM.assignee_id == assignee_id)
        if statuses:
            query = query.filter(TaskORM.status.in_(statuses))
        if parent_task_id is not None:
            query = query.filter(TaskORM.parent_task_id == parent_task_id)

        result = []
        for row in query.order_by(TaskORM.created_at.asc()).all():
            task = self._to_domain(row)
            if tags and not (set(tags) & set(task.tags)):
                continue
            if is_admin or task.assignee_id == user_id:
                result.append(task)
                continue
            if permission_service.can_view_task_via_meeting(task, user_id):
                result.append(task)
                continue
            if task.list_id is None:
                if task.created_by == user_id or permission_service.can_view_task_via_department(task, user_id):
                    result.append(task)
                continue
            role = permission_service.get_role(task.list_id, user_id)
            if permission_service.is_task_visible(task, role=role, user_id=user_id, is_global_admin=is_admin):
                result.append(task)
            elif permission_service.can_view_task_via_department(task, user_id):
                result.append(task)
        return result

    def create(self, *, list_id=None, parent_task_id=None, title, description="", status="open",
               priority="medium", assignee_id=None, watcher_ids=None, due_date=None, start_date=None,
               recurrence_template_id=None, tags=None, pinned=False, created_by=None,
               meeting_id=None, occurrence_id=None):
        timestamp = now_iso()
        row = TaskORM(
            id=new_id(), list_id=list_id, parent_task_id=parent_task_id,
            meeting_id=meeting_id, occurrence_id=occurrence_id,
            recurrence_template_id=recurrence_template_id, title=title,
            description=description, status=status, priority=priority,
            assignee_id=assignee_id, created_by=created_by, updated_by=created_by,
            due_date=due_date, start_date=start_date, pinned=pinned,
            display_standalone=False, created_at=timestamp, updated_at=timestamp,
            last_activity_at=timestamp, completed_at=None,
        )
        db.session.add(row)
        for tag in (tags or []):
            db.session.add(TaskTagORM(task_id=row.id, tag=tag))
        for watcher_id in (watcher_ids or []):
            db.session.add(TaskWatcherORM(task_id=row.id, user_id=watcher_id))
        db.session.commit()
        return self._to_domain(row)

    def update(self, task_id: str, patch: dict, *, updated_by=None, touch_only=False):
        row = TaskORM.query.get(task_id)
        if row is None:
            return None
        simple_fields = {
            "title": "title", "description": "description", "status": "status",
            "priority": "priority", "assignee_id": "assignee_id", "due_date": "due_date",
            "start_date": "start_date", "pinned": "pinned", "display_standalone": "display_standalone",
            "completed_at": "completed_at", "meeting_id": "meeting_id", "occurrence_id": "occurrence_id",
        }
        if not touch_only:
            for key, attr in simple_fields.items():
                if key in patch:
                    setattr(row, attr, patch[key])
            if "tags" in patch:
                TaskTagORM.query.filter_by(task_id=task_id).delete()
                for tag in patch["tags"] or []:
                    db.session.add(TaskTagORM(task_id=task_id, tag=tag))
            if "watcher_ids" in patch:
                TaskWatcherORM.query.filter_by(task_id=task_id).delete()
                for watcher_id in patch["watcher_ids"] or []:
                    db.session.add(TaskWatcherORM(task_id=task_id, user_id=watcher_id))
        row.updated_by = updated_by
        row.updated_at = now_iso()
        row.last_activity_at = now_iso()
        db.session.commit()
        return self._to_domain(row)

    def complete(self, task_id: str, *, updated_by=None):
        return self.update(task_id, {"status": "done", "completed_at": now_iso()}, updated_by=updated_by)

    def reopen(self, task_id: str, *, updated_by=None):
        return self.update(task_id, {"status": "open", "completed_at": None}, updated_by=updated_by)

    def delete(self, task_id: str) -> bool:
        row = TaskORM.query.get(task_id)
        if row is None:
            return False
        db.session.delete(row)
        db.session.commit()
        return True

    def touch_activity(self, task_id: str):
        return self.update(task_id, {}, touch_only=True)
