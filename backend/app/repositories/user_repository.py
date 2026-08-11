"""
UserRepository -- слой доступа к данным для ресурса `users`. Содержит
только SQLAlchemy-запросы, возвращает domain-объекты (app.domain.entities.User)
через уже существующий app.mappers.orm_to_domain -- без какой-либо бизнес-
логики/авторизации (это задача route/permission_service).
"""

from app.extensions import db
from app.mappers import orm_to_domain
from app.models import UserORM
from app.repositories.common import now_iso


class UserRepository:
    def get_all_active(self):
        rows = UserORM.query.filter_by(is_active=True).order_by(UserORM.name.asc()).all()
        return [orm_to_domain.user(row) for row in rows]

    def get_all(self):
        rows = UserORM.query.order_by(UserORM.name.asc()).all()
        return [orm_to_domain.user(row) for row in rows]

    def get_by_id(self, user_id: str):
        row = UserORM.query.get(user_id)
        return orm_to_domain.user(row) if row else None

    def update(self, user_id: str, *, global_role=None, is_active=None):
        """Точечное обновление только тех полей, что переданы (не None).

        globalRole/isActive -- единственные поля, которые сейчас реально меняет
        UsersView.vue (см. src/views/UsersView.vue: usersStore.updateUser(id, { globalRole })
        и usersStore.updateUser(id, { isActive })).
        """
        row = UserORM.query.get(user_id)
        if row is None:
            return None
        if global_role is not None:
            row.global_role = global_role
        if is_active is not None:
            row.is_active = is_active
        row.updated_at = now_iso()
        db.session.commit()
        return orm_to_domain.user(row)
