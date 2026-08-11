"""
UserRepository -- слой доступа к данным для ресурса `users`. Содержит
только SQLAlchemy-запросы, возвращает domain-объекты (app.domain.entities.User)
через уже существующий app.mappers.orm_to_domain -- без какой-либо бизнес-
логики/авторизации (это задача route/permission_service).
"""

from app.extensions import db
from app.mappers import orm_to_domain
from app.models import UserORM
from app.repositories.common import new_id, now_iso


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

    def get_by_login(self, login: str):
        row = UserORM.query.filter_by(login=login).first()
        return orm_to_domain.user(row) if row else None

    def create(self, *, login, name, email, password_hash, global_role="user"):
        """Создание пользователя администратором через POST /api/users.

        Зеркалирует поля, которые уже заполняет app.auth.seed.seed_initial_users --
        та же схема хэширования пароля (werkzeug generate_password_hash), тот же
        набор обязательных полей (login/name/email), только вызывается на лету,
        а не один раз при пустой БД.
        """
        row = UserORM(
            id=new_id(),
            name=name,
            email=email,
            login=login,
            password_hash=password_hash,
            timezone="Europe/Moscow",
            global_role=global_role,
            is_active=True,
            created_at=now_iso(),
            updated_at=now_iso(),
        )
        db.session.add(row)
        db.session.commit()
        return orm_to_domain.user(row)

    def set_password_hash(self, user_id: str, password_hash: str):
        """Сброс пароля администратором (POST /api/users/:id/reset-password)."""
        row = UserORM.query.get(user_id)
        if row is None:
            return None
        row.password_hash = password_hash
        row.updated_at = now_iso()
        db.session.commit()
        return orm_to_domain.user(row)
