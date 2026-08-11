"""
NotificationRepository -- CRUD для NotificationORM + mark-all-read.

Временное решение (см. backend/README.md, раздел "Client/server split"):
due_soon/overdue уведомления в http-режиме пока создаются фронтом через
POST /notifications (клиент сам отслеживает due_date задач и решает, когда
создать уведомление). Перенос этой логики на сервер (background job/scheduler,
сканирующий due_date всех задач) -- задача Промпта 19, здесь не реализуется.
"""

from app.extensions import db
from app.mappers import orm_to_domain
from app.models import NotificationORM
from app.repositories.common import new_id, now_iso


class NotificationRepository:
    def _to_domain(self, row: NotificationORM):
        return orm_to_domain.notification(row)

    def get_by_user_id(self, user_id: str):
        rows = (
            NotificationORM.query.filter_by(user_id=user_id)
            .order_by(NotificationORM.created_at.desc())
            .all()
        )
        return [self._to_domain(row) for row in rows]

    def get_by_id(self, notification_id: str):
        row = NotificationORM.query.get(notification_id)
        return self._to_domain(row) if row else None

    def create(self, *, user_id, type, title, body="", task_id=None, list_id=None, actor_id=None):
        row = NotificationORM(
            id=new_id(), user_id=user_id, type=type, title=title, body=body,
            task_id=task_id, list_id=list_id, actor_id=actor_id, read=False, created_at=now_iso(),
        )
        db.session.add(row)
        db.session.commit()
        return self._to_domain(row)

    def update(self, notification_id: str, patch: dict):
        row = NotificationORM.query.get(notification_id)
        if row is None:
            return None
        if "read" in patch:
            row.read = patch["read"]
        db.session.commit()
        return self._to_domain(row)

    def mark_all_read(self, user_id: str) -> int:
        rows = NotificationORM.query.filter_by(user_id=user_id, read=False).all()
        for row in rows:
            row.read = True
        db.session.commit()
        return len(rows)

    def delete(self, notification_id: str) -> bool:
        row = NotificationORM.query.get(notification_id)
        if row is None:
            return False
        db.session.delete(row)
        db.session.commit()
        return True
