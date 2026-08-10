"""
Пакет backend-сервисов, работающих только с domain-объектами
(app.domain.entities) и ORM (app.models) для query, но не с DTO/HTTP.
"""

from app.services.permission_service import permission_service, PermissionService

__all__ = ["permission_service", "PermissionService"]
