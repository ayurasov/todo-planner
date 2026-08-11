"""
Репозитории вложенных подресурсов задачи: checklist-items, notes, comments.
Собственных проверок прав здесь нет -- они вычисляются в routes по
правилам родительской задачи (см. app.tasks.routes).
"""

from app.extensions import db
from app.mappers import orm_to_domain
from app.models import ChecklistItemORM, CommentMentionORM, CommentORM, NoteORM
from app.repositories.common import new_id, now_iso


class ChecklistItemRepository:
    def get_by_task_id(self, task_id: str):
        rows = ChecklistItemORM.query.filter_by(task_id=task_id).order_by(ChecklistItemORM.order_index.asc()).all()
        return [orm_to_domain.checklist_item(row) for row in rows]

    def get_by_id(self, item_id: str):
        row = ChecklistItemORM.query.get(item_id)
        return orm_to_domain.checklist_item(row) if row else None

    def create(self, *, task_id, title, done=False, order=0, recurrence_scope="instance_only"):
        row = ChecklistItemORM(
            id=new_id(), task_id=task_id, title=title, done=done,
            order_index=order, recurrence_scope=recurrence_scope,
        )
        db.session.add(row)
        db.session.commit()
        return orm_to_domain.checklist_item(row)

    def update(self, item_id: str, patch: dict):
        row = ChecklistItemORM.query.get(item_id)
        if row is None:
            return None
        if "title" in patch:
            row.title = patch["title"]
        if "done" in patch:
            row.done = patch["done"]
        if "order" in patch:
            row.order_index = patch["order"]
        if "recurrence_scope" in patch:
            row.recurrence_scope = patch["recurrence_scope"]
        db.session.commit()
        return orm_to_domain.checklist_item(row)

    def delete(self, item_id: str) -> bool:
        row = ChecklistItemORM.query.get(item_id)
        if row is None:
            return False
        db.session.delete(row)
        db.session.commit()
        return True


class NoteRepository:
    def get_by_task_id(self, task_id: str):
        rows = NoteORM.query.filter_by(task_id=task_id).order_by(NoteORM.created_at.asc()).all()
        return [orm_to_domain.note(row) for row in rows]

    def get_by_id(self, note_id: str):
        row = NoteORM.query.get(note_id)
        return orm_to_domain.note(row) if row else None

    def create(self, *, task_id, content_json=None, updated_by=None):
        timestamp = now_iso()
        row = NoteORM(
            id=new_id(), task_id=task_id,
            content=self._dump(content_json or {"type": "doc", "content": []}),
            updated_by=updated_by, created_at=timestamp, updated_at=timestamp,
        )
        db.session.add(row)
        db.session.commit()
        return orm_to_domain.note(row)

    def update(self, note_id: str, *, content_json=None, updated_by=None):
        row = NoteORM.query.get(note_id)
        if row is None:
            return None
        if content_json is not None:
            row.content = self._dump(content_json)
        row.updated_by = updated_by
        row.updated_at = now_iso()
        db.session.commit()
        return orm_to_domain.note(row)

    @staticmethod
    def _dump(content_json):
        import json
        return json.dumps(content_json)


class CommentRepository:
    def get_by_task_id(self, task_id: str):
        rows = CommentORM.query.filter_by(task_id=task_id).order_by(CommentORM.created_at.asc()).all()
        return [self._to_domain(row) for row in rows]

    def get_by_id(self, comment_id: str):
        row = CommentORM.query.get(comment_id)
        return self._to_domain(row) if row else None

    def _to_domain(self, row: CommentORM):
        mention_rows = CommentMentionORM.query.filter_by(comment_id=row.id).all()
        mentions = [m.user_id for m in mention_rows]
        return orm_to_domain.comment(row, mentions=mentions)

    def create(self, *, task_id, author_id, text, mentions=None):
        row = CommentORM(
            id=new_id(), task_id=task_id, author_id=author_id, text=text,
            created_at=now_iso(), edited_at=None,
        )
        db.session.add(row)
        for user_id in (mentions or []):
            db.session.add(CommentMentionORM(comment_id=row.id, user_id=user_id))
        db.session.commit()
        return self._to_domain(row)

    def update(self, comment_id: str, *, text=None, mentions=None):
        row = CommentORM.query.get(comment_id)
        if row is None:
            return None
        if text is not None:
            row.text = text
            row.edited_at = now_iso()
        if mentions is not None:
            CommentMentionORM.query.filter_by(comment_id=comment_id).delete()
            for user_id in mentions:
                db.session.add(CommentMentionORM(comment_id=comment_id, user_id=user_id))
        db.session.commit()
        return self._to_domain(row)

    def delete(self, comment_id: str) -> bool:
        row = CommentORM.query.get(comment_id)
        if row is None:
            return False
        db.session.delete(row)
        db.session.commit()
        return True
