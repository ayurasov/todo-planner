"""
DepartmentRepository -- CRUD плоского справочника отделов/служб (DepartmentORM)
и управление связью many-to-many "руководитель -- отделы" (ManagerDepartmentORM).
Содержит только SQLAlchemy-запросы, возвращает domain-объекты.
"""

from app.extensions import db
from app.mappers import orm_to_domain
from app.models import DepartmentORM, ManagerDepartmentORM
from app.repositories.common import new_id, now_iso


class DepartmentRepository:
    def get_all(self):
        rows = DepartmentORM.query.order_by(DepartmentORM.name.asc()).all()
        return [orm_to_domain.department(row) for row in rows]

    def get_by_id(self, department_id: str):
        row = DepartmentORM.query.get(department_id)
        return orm_to_domain.department(row) if row else None

    def get_by_name(self, name: str):
        row = DepartmentORM.query.filter_by(name=name).first()
        return orm_to_domain.department(row) if row else None

    def create(self, *, name: str):
        row = DepartmentORM(
            id=new_id(), name=name, created_at=now_iso(), updated_at=now_iso(),
        )
        db.session.add(row)
        db.session.commit()
        return orm_to_domain.department(row)

    def update(self, department_id: str, *, name=None):
        row = DepartmentORM.query.get(department_id)
        if row is None:
            return None
        if name is not None:
            row.name = name
        row.updated_at = now_iso()
        db.session.commit()
        return orm_to_domain.department(row)

    def delete(self, department_id: str) -> bool:
        row = DepartmentORM.query.get(department_id)
        if row is None:
            return False
        db.session.delete(row)  # ON DELETE CASCADE/SET NULL -- см. models.py
        db.session.commit()
        return True

    def get_manager_ids(self, department_id: str):
        rows = ManagerDepartmentORM.query.filter_by(department_id=department_id).all()
        return [row.user_id for row in rows]

    def get_managed_department_ids(self, user_id: str):
        """Отделы, которыми управляет данный руководитель (могут быть несколько)."""
        rows = ManagerDepartmentORM.query.filter_by(user_id=user_id).all()
        return [row.department_id for row in rows]

    def set_managers(self, department_id: str, user_ids: list):
        """Полная зациска -- текущий список руководителей отдела заменяется
        переданным (каждый руководитель при этом может оставаться руководителем других
        отделов -- затрагивается только связка с этим department_id)."""
        ManagerDepartmentORM.query.filter_by(department_id=department_id).delete()
        for user_id in user_ids:
            db.session.add(ManagerDepartmentORM(user_id=user_id, department_id=department_id))
        db.session.commit()
        return self.get_manager_ids(department_id)
