"""
ListRepository -- слой доступа к данным для ресурса `lists` и вложенных
`list_memberships`. Содержит только SQLAlchemy-запросы, возвращает domain-
объекты через app.mappers.orm_to_domain. Права доступа (кто видит/может
удалять список) проверяются не здесь, а в route-слое через
@require_list_permission (см. app.services.permission_service).
"""

from app.extensions import db
from app.mappers import orm_to_domain
from app.models import ListMembershipORM, ListORM
from app.repositories.common import new_id, now_iso
from app.services.permission_service import LIST_ROLE_OWNER, permission_service


class ListRepository:
    def _owner_ids(self, list_id: str):
        rows = ListMembershipORM.query.filter_by(list_id=list_id, role=LIST_ROLE_OWNER).all()
        return [row.user_id for row in rows]

    def _to_domain(self, row: ListORM):
        return orm_to_domain.todo_list(row, owner_ids=self._owner_ids(row.id))

    def get_accessible(self, user_id: str):
        """Списки, доступные текущему пользователю (все для global admin,
        иначе -- только те, где есть membership), согласно
        permission_service.get_accessible_list_ids.
        """
        list_ids = permission_service.get_accessible_list_ids(user_id)
        if not list_ids:
            return []
        rows = ListORM.query.filter(ListORM.id.in_(list_ids)).order_by(ListORM.order_index.asc()).all()
        return [self._to_domain(row) for row in rows]

    def get_by_id(self, list_id: str):
        row = ListORM.query.get(list_id)
        return self._to_domain(row) if row else None

    def create(self, *, title, description="", color="#4f7cff", is_shared=False,
               default_view="list", settings=None, owner_id=None):
        row = ListORM(
            id=new_id(),
            title=title,
            description=description,
            color=color,
            is_shared=is_shared,
            default_view=default_view,
            settings=settings or {},
            archived=False,
            order_index=0,
            created_at=now_iso(),
            updated_at=now_iso(),
        )
        db.session.add(row)
        # flush() гарантированно выполняет INSERT в "lists" до создания membership,
        # независимо от того, как SQLAlchemy unit-of-work авто-упорядочивает объекты
        # в одной транзакции -- защита от ForeignKeyViolation на list_memberships.list_id
        # (наблюдалось после restart воркера с "грязной" сессией из-за прошлых ошибок).
        db.session.flush()
        if owner_id:
            membership = ListMembershipORM(
                id=new_id(), list_id=row.id, user_id=owner_id,
                role=LIST_ROLE_OWNER, added_at=now_iso(),
            )
            db.session.add(membership)
        db.session.commit()
        return self._to_domain(row)

    def update(self, list_id: str, patch: dict):
        row = ListORM.query.get(list_id)
        if row is None:
            return None
        if "title" in patch:
            row.title = patch["title"]
        if "description" in patch:
            row.description = patch["description"]
        if "color" in patch:
            row.color = patch["color"]
        if "is_shared" in patch:
            row.is_shared = patch["is_shared"]
        if "default_view" in patch:
            row.default_view = patch["default_view"]
        if "settings" in patch and patch["settings"] is not None:
            row.settings = patch["settings"]
        if "archived" in patch and patch["archived"] is not None:
            row.archived = patch["archived"]
        if "order" in patch and patch["order"] is not None:
            row.order_index = patch["order"]
        row.updated_at = now_iso()
        db.session.commit()
        return self._to_domain(row)

    def delete(self, list_id: str) -> bool:
        row = ListORM.query.get(list_id)
        if row is None:
            return False
        db.session.delete(row)
        db.session.commit()
        return True

    def get_members(self, list_id: str):
        rows = ListMembershipORM.query.filter_by(list_id=list_id).order_by(ListMembershipORM.added_at.asc()).all()
        return [orm_to_domain.list_membership(row) for row in rows]

    def add_or_update_member(self, list_id: str, user_id: str, role: str):
        existing = ListMembershipORM.query.filter_by(list_id=list_id, user_id=user_id).first()
        if existing:
            existing.role = role
            db.session.commit()
            return orm_to_domain.list_membership(existing)
        row = ListMembershipORM(
            id=new_id(), list_id=list_id, user_id=user_id, role=role, added_at=now_iso(),
        )
        db.session.add(row)
        db.session.commit()
        return orm_to_domain.list_membership(row)

    def remove_member(self, list_id: str, user_id: str) -> bool:
        row = ListMembershipORM.query.filter_by(list_id=list_id, user_id=user_id).first()
        if row is None:
            return False
        db.session.delete(row)
        db.session.commit()
        return True
