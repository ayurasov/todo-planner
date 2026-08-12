"""
UserRepository -- слой доступа к данным для ресурса `users`. Содержит
только SQLAlchemy-запросы, возвращает domain-объекты (app.domain.entities.User)
через уже существующий app.mappers.orm_to_domain -- без какой-либо бизнес-
логики/авторизации (это задача route/permission_service).
"""

from app.extensions import db
from app.mappers import orm_to_domain
from app.models import ManagerDepartmentORM, UserORM
from app.repositories.common import new_id, now_iso


class DuplicateEmailError(Exception):
    """Email уже занят другим пользователем (уникальность на уровне users.email)."""


class DuplicateLoginError(Exception):
    """Login уже занят другим пользователем (уникальность на уровне users.login)."""


class UserRepository:
    def _managed_department_ids(self, user_id: str):
        rows = ManagerDepartmentORM.query.filter_by(user_id=user_id).all()
        return [row.department_id for row in rows]

    def _to_domain(self, row: UserORM):
        return orm_to_domain.user(row, managed_department_ids=self._managed_department_ids(row.id))

    def get_all_active(self):
        rows = UserORM.query.filter_by(is_active=True).order_by(UserORM.name.asc()).all()
        return [self._to_domain(row) for row in rows]

    def get_all(self):
        rows = UserORM.query.order_by(UserORM.name.asc()).all()
        return [self._to_domain(row) for row in rows]

    def get_by_id(self, user_id: str):
        row = UserORM.query.get(user_id)
        return self._to_domain(row) if row else None

    def get_by_email(self, email: str):
        row = UserORM.query.filter_by(email=email).first()
        return self._to_domain(row) if row else None

    def update(self, user_id: str, *, global_role=None, is_active=None,
               name=None, email=None, position=None, department=None,
               department_id=None, clear_department_id=False,
               managed_department_ids=None):
        """Точечное обновление только тех полей, что переданы (не None).

        position/department -- старые свободные текстовые справочные поля (должность/отдел),
        department_id -- ссылка на новый плоский справочник Department (clear_department_id=True
        явно сбрасывает в NULL, т.к. None от department_id не отличить от "не менять").
        managed_department_ids -- полная замена списка отделов, которыми руководит
        данный руководитель (может быть несколько отделов/служб одновременно).

        Перед изменением email заранее проверяем уникальность (см. DuplicateEmailError) --
        иначе IntegrityError от UNIQUE-констрейнта users.email долетал бы до route как
        необработанное исключение (500) вместо аккуратной 400-ошибки валидации (см.
        incident: "не могу создать пользователя с правами руководитель / присвоить права
        руководителя" -- 500 из-за совпавшего email при одновременном изменении роли).
        """
        row = UserORM.query.get(user_id)
        if row is None:
            return None

        if email is not None and email != row.email:
            existing = UserORM.query.filter(UserORM.email == email, UserORM.id != user_id).first()
            if existing is not None:
                raise DuplicateEmailError(email)

        if global_role is not None:
            row.global_role = global_role
        if is_active is not None:
            row.is_active = is_active
        if name is not None:
            row.name = name
        if email is not None:
            row.email = email
        if position is not None:
            row.position = position
        if department is not None:
            row.department = department
        if clear_department_id:
            row.department_id = None
        elif department_id is not None:
            row.department_id = department_id
        row.updated_at = now_iso()

        if managed_department_ids is not None:
            ManagerDepartmentORM.query.filter_by(user_id=user_id).delete()
            for department_id_value in managed_department_ids:
                db.session.add(ManagerDepartmentORM(user_id=user_id, department_id=department_id_value))

        db.session.commit()
        return self._to_domain(row)

    def delete(self, user_id: str) -> bool:
        """Полное удаление пользователя (hard delete).

        FK на users.id в остальных таблицах уже настроены с ondelete=CASCADE
        (участия в списках/watcher/reactions и т.п., включая manager_departments) или
        ondelete=SET NULL (created_by/assignee_id/updated_by/actor_id/author_id) на уровне
        схемы БД (см. backend/app/models/models.py) -- поэтому удаление строки
        users безопасно и не оставляет висячих ссылок.
        """
        row = UserORM.query.get(user_id)
        if row is None:
            return False
        db.session.delete(row)
        db.session.commit()
        return True

    def get_by_login(self, login: str):
        row = UserORM.query.filter_by(login=login).first()
        return self._to_domain(row) if row else None

    def create(self, *, login, name, email, password_hash, global_role="user",
               position=None, department=None, department_id=None):
        """Создание пользователя администратором через POST /api/users.

        Зеркалирует поля, которые уже заполняет app.auth.seed.seed_initial_users --
        та же схема хэширования пароля (werkzeug generate_password_hash), тот же
        набор обязательных полей (login/name/email), только вызывается на лету,
        а не один раз при пустой БД.

        Уникальность login/email проверяется явно до INSERT (см. DuplicateLoginError/
        DuplicateEmailError) -- иначе IntegrityError от UNIQUE-констрейнта долетал бы
        до route как необработанное исключение (500) вместо 400 validation_error.
        Проверка login уже была в routes.create_user, но email не проверялся вовсе --
        именно это приводило к 500 при создании пользователя с ролью 'manager', если
        email случайно совпадал с уже существующим (в т.ч. seed-пользователями).
        """
        if UserORM.query.filter_by(login=login).first() is not None:
            raise DuplicateLoginError(login)
        if UserORM.query.filter_by(email=email).first() is not None:
            raise DuplicateEmailError(email)

        row = UserORM(
            id=new_id(),
            name=name,
            email=email,
            login=login,
            password_hash=password_hash,
            timezone="Europe/Moscow",
            global_role=global_role,
            is_active=True,
            position=position,
            department=department,
            department_id=department_id,
            created_at=now_iso(),
            updated_at=now_iso(),
        )
        db.session.add(row)
        db.session.commit()
        return self._to_domain(row)

    def set_password_hash(self, user_id: str, password_hash: str):
        """Сброс пароля администратором (POST /api/users/:id/reset-password)."""
        row = UserORM.query.get(user_id)
        if row is None:
            return None
        row.password_hash = password_hash
        row.updated_at = now_iso()
        db.session.commit()
        return self._to_domain(row)
