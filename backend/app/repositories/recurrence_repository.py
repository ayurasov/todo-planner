"""
RecurrenceRepository -- CRUD для RecurrenceTemplateORM и порт логики
`src/services/RecurrenceService.js` (computeNextOccurrence / onTaskCompleted)
на backend.

Зачем: в http-режиме генерация следующего инстанса задачи для
COMPLETION_BASED-шаблона должна выполняться в момент complete_task на backend
(единый источник правды, независимо от того, какой клиент завершил
задачу), а не только на фронте -- см. app/tasks/routes.py update_task и
backend/README.md, раздел "Client/server split".
"""

from datetime import datetime, timedelta, timezone

from app.domain.entities import RecurrenceTemplate
from app.extensions import db
from app.mappers import orm_to_domain
from app.models import RecurrenceTemplateORM
from app.repositories.common import new_id, now_iso

RECURRENCE_TYPE_COMPLETION_BASED = "completion_based"
RECURRENCE_FREQ_DAILY = "daily"
RECURRENCE_FREQ_WEEKLY = "weekly"
RECURRENCE_FREQ_MONTHLY = "monthly"


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _last_day_in_month(year: int, month: int) -> int:
    next_first = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
    return (next_first - timedelta(days=1)).day


def compute_next_occurrence(from_date: str, rule: dict) -> datetime:
    """1:1 порт `RecurrenceService.js.computeNextOccurrence`.

    Для MONTHLY учитывает edge case "целевой день не существует в месяце"
    (например 31 в апреле) -- в этом случае берётся последний день целевого месяца.
    """
    base = _parse_iso(from_date) if from_date else datetime.now(timezone.utc)
    freq = rule.get("freq", RECURRENCE_FREQ_DAILY)
    interval = rule.get("interval") or 1

    if freq == RECURRENCE_FREQ_DAILY:
        return base + timedelta(days=interval)
    if freq == RECURRENCE_FREQ_WEEKLY:
        return base + timedelta(days=7 * interval)
    if freq == RECURRENCE_FREQ_MONTHLY:
        total_month_index = base.month - 1 + interval
        target_year = base.year + total_month_index // 12
        target_month = total_month_index % 12 + 1
        target_day = rule.get("byMonthDay") or base.day
        last_day = _last_day_in_month(target_year, target_month)
        safe_day = min(target_day, last_day)
        return base.replace(year=target_year, month=target_month, day=safe_day)
    return base + timedelta(days=interval)


class RecurrenceRepository:
    def _to_domain(self, row: RecurrenceTemplateORM) -> RecurrenceTemplate:
        return orm_to_domain.recurrence_template(row)

    def get_all(self, list_id=None):
        query = RecurrenceTemplateORM.query
        if list_id:
            query = query.filter_by(list_id=list_id)
        rows = query.order_by(RecurrenceTemplateORM.id.asc()).all()
        return [self._to_domain(row) for row in rows]

    def get_by_id(self, template_id: str):
        row = RecurrenceTemplateORM.query.get(template_id)
        return self._to_domain(row) if row else None

    def create(self, *, list_id, title_template, type, rule=None, timezone="Europe/Moscow",
               generate_ahead_count=1, checklist_template=None):
        row = RecurrenceTemplateORM(
            id=new_id(), list_id=list_id, title_template=title_template, type=type,
            rule=rule or {}, timezone=timezone, generate_ahead_count=generate_ahead_count,
            last_generated_instance_date=None, checklist_template=checklist_template or [],
        )
        db.session.add(row)
        db.session.commit()
        return self._to_domain(row)

    def update(self, template_id: str, patch: dict):
        row = RecurrenceTemplateORM.query.get(template_id)
        if row is None:
            return None
        simple_fields = {
            "title_template": "title_template", "timezone": "timezone",
            "generate_ahead_count": "generate_ahead_count",
            "last_generated_instance_date": "last_generated_instance_date",
        }
        for key, attr in simple_fields.items():
            if key in patch:
                setattr(row, attr, patch[key])
        if "rule" in patch:
            row.rule = patch["rule"] or {}
        if "checklist_template" in patch:
            row.checklist_template = patch["checklist_template"] or []
        db.session.commit()
        return self._to_domain(row)

    def delete(self, template_id: str) -> bool:
        row = RecurrenceTemplateORM.query.get(template_id)
        if row is None:
            return False
        db.session.delete(row)
        db.session.commit()
        return True

    def generate_next_instance(self, template: RecurrenceTemplate, from_task, *, task_repository):
        """Порт `RecurrenceService.js.generateNextInstance`: создаёт следующую задачу
        серии и обновляет last_generated_instance_date у шаблона. `task_repository`
        передаётся снаружи, чтобы не создавать циклический импорт с TaskRepository."""
        from_date = (from_task.due_date if from_task else None) or now_iso()
        next_dt = compute_next_occurrence(from_date, template.rule or {})
        next_iso = next_dt.isoformat()
        new_task = task_repository.create(
            list_id=template.list_id,
            title=template.title_template,
            due_date=next_iso,
            recurrence_template_id=template.id,
            assignee_id=from_task.assignee_id if from_task else None,
            created_by=from_task.created_by if from_task else None,
        )
        self.update(template.id, {"last_generated_instance_date": next_iso})
        return new_task

    def on_task_completed(self, task, *, task_repository):
        """Порт `RecurrenceService.js.onTaskCompleted`: вызывается из tasks/routes.py update_task
        при переводе задачи в status=done. fixed_schedule-шаблоны не генерируются
        здесь -- их инстансы создаются заранее (см. Промпт 19 про background jobs)."""
        if not task or not task.recurrence_template_id:
            return None
        template = self.get_by_id(task.recurrence_template_id)
        if not template:
            return None
        if template.type != RECURRENCE_TYPE_COMPLETION_BASED:
            return None
        return self.generate_next_instance(template, task, task_repository=task_repository)
