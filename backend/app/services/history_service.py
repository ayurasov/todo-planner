"""
Порт frontend `src/services/HistoryService.js` на backend: все мутации задачи
должны проходить через этот сервис, гарантируя запись audit trail в
`task_history_entries` (см. backend/migrations). В отличие от frontend-версии,
здесь это единственный источник истины — backend сам пишет записи в
момент мутации (create/update/complete/reopen/assign/reschedule/comment),
поэтому `HttpHistoryRepository.append()` на фронтенде — no-op.

Формат old_value/new_value — текст (столбец TEXT в task_history_entries),
поэтому не-строковые значения приводятся к str(...) (None -> None).
"""

from app.extensions import db
from app.mappers import orm_to_domain
from app.models import TaskHistoryEntryORM
from app.repositories.common import new_id, now_iso

HISTORY_CREATED = "created"
HISTORY_FIELD_CHANGED = "field_changed"
HISTORY_COMMENTED = "commented"
HISTORY_ASSIGNEE_CHANGED = "assignee_changed"
HISTORY_RESCHEDULED = "rescheduled"
HISTORY_COMPLETED = "completed"
HISTORY_REOPENED = "reopened"


def _stringify(value):
    if value is None:
        return None
    return str(value)


class HistoryService:
    def _append(self, *, task_id, actor_id, type_, field=None, old_value=None, new_value=None, comment=None):
        row = TaskHistoryEntryORM(
            id=new_id(),
            task_id=task_id,
            actor_id=actor_id,
            timestamp=now_iso(),
            type=type_,
            field=field,
            old_value=_stringify(old_value),
            new_value=_stringify(new_value),
            comment=comment,
        )
        db.session.add(row)
        db.session.commit()
        return orm_to_domain.history_entry(row)

    def record_created(self, task_id, actor_id):
        return self._append(task_id=task_id, actor_id=actor_id, type_=HISTORY_CREATED)

    def record_field_changed(self, task_id, actor_id, field, old_value, new_value):
        if old_value == new_value:
            return None
        return self._append(
            task_id=task_id, actor_id=actor_id, type_=HISTORY_FIELD_CHANGED,
            field=field, old_value=old_value, new_value=new_value,
        )

    def record_assignee_changed(self, task_id, actor_id, old_value, new_value):
        return self._append(
            task_id=task_id, actor_id=actor_id, type_=HISTORY_ASSIGNEE_CHANGED,
            old_value=old_value, new_value=new_value,
        )

    def record_rescheduled(self, task_id, actor_id, old_value, new_value):
        return self._append(
            task_id=task_id, actor_id=actor_id, type_=HISTORY_RESCHEDULED,
            old_value=old_value, new_value=new_value,
        )

    def record_completed(self, task_id, actor_id):
        return self._append(task_id=task_id, actor_id=actor_id, type_=HISTORY_COMPLETED)

    def record_reopened(self, task_id, actor_id):
        return self._append(task_id=task_id, actor_id=actor_id, type_=HISTORY_REOPENED)

    def record_comment(self, task_id, actor_id, comment_text):
        return self._append(task_id=task_id, actor_id=actor_id, type_=HISTORY_COMMENTED, comment=comment_text)

    def get_task_timeline(self, task_id):
        rows = TaskHistoryEntryORM.query.filter_by(task_id=task_id).order_by(TaskHistoryEntryORM.timestamp.asc()).all()
        return [orm_to_domain.history_entry(row) for row in rows]


history_service = HistoryService()
