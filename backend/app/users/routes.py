"""
Реализация blueprint 'users' поверх UserRepository (app.repositories).
Автентификация — глобальным guard в app.auth.security (401 для всего blueprint).
PATCH /users/:id доступен только global admin (PermissionService.is_global_admin) --
зеркало frontend-правила UsersView.vue (редактировать роль/активность
других пользователей может только админ).
"""

from flask import jsonify, request
from pydantic import ValidationError

from app.auth.security import current_user_id
from app.dto import UserResponseDTO
from app.mappers import domain_to_dto
from app.repositories import UserRepository
from app.services.permission_service import permission_denied_response, permission_service
from app.users import users_bp

user_repository = UserRepository()


def _not_found(name="user"):
    return jsonify({"error": "not_found", "message": f"{name} не найден"}), 404


def _validation_error(exc: ValidationError):
    return jsonify({"error": "validation_error", "details": exc.errors()}), 400


@users_bp.route("", methods=["GET"])
def list_users(**kwargs):
    users = user_repository.get_all_active()
    return jsonify([domain_to_dto.user(u).model_dump(by_alias=True) for u in users])


@users_bp.route("/<string:user_id>", methods=["GET"])
def get_user(user_id, **kwargs):
    user = user_repository.get_by_id(user_id)
    if user is None:
        return _not_found()
    return jsonify(domain_to_dto.user(user).model_dump(by_alias=True))


@users_bp.route("/<string:user_id>", methods=["PATCH"])
def update_user(user_id, **kwargs):
    if not permission_service.is_global_admin(current_user_id()):
        return permission_denied_response("Сменять пользователя может только администратор")

    payload = request.get_json(silent=True) or {}
    try:
        # частичный PATCH: читаем только те поля, которые реально пришли в запросе
        allowed = {"globalRole", "isActive"}
        unknown = set(payload) - allowed
        if unknown:
            raise ValidationError.from_exception_data(
                "UserUpdate", [{"type": "extra_forbidden", "loc": (k,), "input": payload[k]} for k in unknown]
            )
    except ValidationError as exc:
        return _validation_error(exc)

    updated = user_repository.update(
        user_id,
        global_role=payload.get("globalRole"),
        is_active=payload.get("isActive"),
    )
    if updated is None:
        return _not_found()
    return jsonify(domain_to_dto.user(updated).model_dump(by_alias=True))
