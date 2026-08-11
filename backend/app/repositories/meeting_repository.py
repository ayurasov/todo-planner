"""
MeetingRepository -- CRUD встреч (MeetingORM), участники (MeetingAttendeeORM)
и подвстречи регулярных серий (MeetingOccurrenceORM).

Агрегация "не выполнено в серии" (unfinishedTotalCount) перенесена на backend
и отдаётся готовым полем в MeetingResponseDTO -- см. решение в backend/README.md,
раздел "Client/server split: meetings/recurrence/notifications". Frontend
(MeetingDetailView.vue unfinishedTotalCount) остаётся как есть и продолжает
сам строить unfinishedGroupsByOccurrence из обычного списка задач (он уже
загружает все tasks серии через GET /tasks?listId=), backend-поле -- только
готовое число для бейджа/заголовка без отдельного запроса задач на странице
списка встреч.
"""

import json

from app.extensions import db
from app.mappers import orm_to_domain
from app.models import MeetingAttendeeORM, MeetingOccurrenceORM, MeetingORM, TaskORM
from app.repositories.common import new_id, now_iso


def _loads(value, default):
    if value is None:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


class MeetingRepository:
    def _attendee_ids(self, meeting_id: str):
        rows = MeetingAttendeeORM.query.filter_by(meeting_id=meeting_id).all()
        return [row.user_id for row in rows]

    def _occurrences(self, meeting_id: str):
        rows = (
            MeetingOccurrenceORM.query.filter_by(meeting_id=meeting_id)
            .order_by(MeetingOccurrenceORM.date.asc())
            .all()
        )
        return [orm_to_domain.meeting_occurrence(row) for row in rows]

    def _to_domain(self, row: MeetingORM):
        return orm_to_domain.meeting(
            row, attendee_ids=self._attendee_ids(row.id), occurrences=self._occurrences(row.id)
        )

    def get_all(self):
        rows = MeetingORM.query.order_by(MeetingORM.order_index.asc(), MeetingORM.created_at.asc()).all()
        return [self._to_domain(row) for row in rows]

    def get_by_id(self, meeting_id: str):
        row = MeetingORM.query.get(meeting_id)
        return self._to_domain(row) if row else None

    def create(self, *, title, date, description="", link="", color="#4f7cff", recurrence=None,
               attendee_ids=None, created_by=None, order=0):
        timestamp = now_iso()
        row = MeetingORM(
            id=new_id(), title=title, date=date, description=description, link=link, color=color,
            archived=False, order_index=order, recurrence=json.dumps(recurrence) if recurrence else None,
            created_by=created_by, created_at=timestamp,
        )
        db.session.add(row)
        for user_id in (attendee_ids or []):
            db.session.add(MeetingAttendeeORM(meeting_id=row.id, user_id=user_id))
        db.session.commit()
        return self._to_domain(row)

    def update(self, meeting_id: str, patch: dict):
        """Атомарный partial update. `occurrences` в patch -- списоргнуть подвстречи
        (каждая запись с dict-полями id/date/description/link) -- порт логики
        meetingsStore.ensureOccurrences/updateOccurrence, которые передают весь список occurrences
        целиком через PATCH."""
        row = MeetingORM.query.get(meeting_id)
        if row is None:
            return None

        simple_fields = {
            "title": "title", "date": "date", "description": "description",
            "link": "link", "color": "color", "archived": "archived", "order": "order_index",
        }
        for key, attr in simple_fields.items():
            if key in patch:
                setattr(row, attr, patch[key])
        if "recurrence" in patch:
            row.recurrence = json.dumps(patch["recurrence"]) if patch["recurrence"] else None
        if "attendee_ids" in patch:
            MeetingAttendeeORM.query.filter_by(meeting_id=meeting_id).delete()
            for user_id in patch["attendee_ids"] or []:
                db.session.add(MeetingAttendeeORM(meeting_id=meeting_id, user_id=user_id))
        if "occurrences" in patch:
            MeetingOccurrenceORM.query.filter_by(meeting_id=meeting_id).delete()
            for occ in patch["occurrences"] or []:
                db.session.add(MeetingOccurrenceORM(
                    id=occ.get("id") or new_id(),
                    meeting_id=meeting_id,
                    date=occ["date"],
                    description=occ.get("description", ""),
                    link=occ.get("link", ""),
                    generated_at=occ.get("generated_at") or now_iso(),
                ))

        db.session.commit()
        return self._to_domain(row)

    def delete(self, meeting_id: str) -> bool:
        row = MeetingORM.query.get(meeting_id)
        if row is None:
            return False
        TaskORM.query.filter_by(meeting_id=meeting_id).update({"meeting_id": None, "occurrence_id": None})
        db.session.delete(row)  # ON DELETE CASCADE -- attendees/occurrences удаляются в базе
        db.session.commit()
        return True

    def list_occurrences(self, meeting_id: str):
        return self._occurrences(meeting_id)

    def unfinished_total_count(self, meeting_id: str) -> int:
        """Аналог MeetingDetailView.vue unfinishedTotalCount: количество задач серии
        встреч (meeting_id == meeting_id), статус которых не done/cancelled."""
        return (
            TaskORM.query.filter(
                TaskORM.meeting_id == meeting_id,
                TaskORM.status.notin_(["done", "cancelled"]),
            ).count()
        )
