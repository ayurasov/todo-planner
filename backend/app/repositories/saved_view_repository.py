"""
SavedViewRepository -- CRUD для SavedViewORM, всегда привязано к user_id
текущего авторизованного пользователя (сохранённые виды -- личные,
не разделяются между пользователями).
"""

from app.extensions import db
from app.mappers import orm_to_domain
from app.models import SavedViewORM
from app.repositories.common import new_id


class SavedViewRepository:
    def _to_domain(self, row: SavedViewORM):
        return orm_to_domain.saved_view(row)

    def get_by_user_id(self, user_id: str):
        rows = SavedViewORM.query.filter_by(user_id=user_id).all()
        return [self._to_domain(row) for row in rows]

    def get_by_id(self, view_id: str):
        row = SavedViewORM.query.get(view_id)
        return self._to_domain(row) if row else None

    def create(self, *, user_id, name, filters=None, sort=None, group_by=None, pinned=False):
        import json
        row = SavedViewORM(
            id=new_id(), user_id=user_id, name=name,
            filters=json.dumps(filters or {}),
            sort=json.dumps(sort or {"field": "score", "dir": "desc"}),
            group_by=group_by, pinned=pinned,
        )
        db.session.add(row)
        db.session.commit()
        return self._to_domain(row)

    def update(self, view_id: str, patch: dict):
        import json
        row = SavedViewORM.query.get(view_id)
        if row is None:
            return None
        if "name" in patch:
            row.name = patch["name"]
        if "filters" in patch:
            row.filters = json.dumps(patch["filters"] or {})
        if "sort" in patch:
            row.sort = json.dumps(patch["sort"] or {"field": "score", "dir": "desc"})
        if "group_by" in patch:
            row.group_by = patch["group_by"]
        if "pinned" in patch:
            row.pinned = patch["pinned"]
        db.session.commit()
        return self._to_domain(row)

    def delete(self, view_id: str) -> bool:
        row = SavedViewORM.query.get(view_id)
        if row is None:
            return False
        db.session.delete(row)
        db.session.commit()
        return True
