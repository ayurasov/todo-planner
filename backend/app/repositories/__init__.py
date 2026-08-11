"""
Пакет repositories-слоя. Единственный слой, которому разрешено выполнять
SQLAlchemy-запросы к БД и напрямую работать с ORM-моделями (app.models).

Возвращает только domain-объекты (app.domain.entities), полученные через
уже существующие app.mappers.orm_to_domain — routes/services дальше не
должны видеть ORM напрямую (см. backend/README.md, раздел "ORM / domain /
DTO слои").
"""

from app.repositories.common import new_id, now_iso
from app.repositories.user_repository import UserRepository
from app.repositories.list_repository import ListRepository

__all__ = ["new_id", "now_iso", "UserRepository", "ListRepository"]
