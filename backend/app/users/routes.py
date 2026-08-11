"""
Реализация blueprint 'users' поверх UserRepository (app.repositories).
Автентификация — глобальным guard в app.auth.security (401 для всего blueprint).
PATCH /users/:id доступен только global admin (PermissionService.is_global_admin) --
зеркало frontend-правила UsersView.vue (редактировать роль/активность
других пользователей может только админ).

POST /users (создание) и POST /users/:id/reset-password -- тоже только global admin.
Пароль (при создании -- заданный явно, при сбросе -- сгенерированный временный)
возвращается в JSON-ответе ОДИН РАЗ, как открытый текст -- аналог поведения
app.auth.seed.seed_initial_users (пароль печатается один раз и не хранится в
открытом виде). Ответственность фронтенда -- показать его администратору сразу
и не сохранять.
"""

import secrets

from flask import jsonify, request
from werkzeug.security import generate_password_hash

from app.auth.security import current_user_id
from app.mappers import domain_to_dto
from app.repositories import UserRepository
from app.services.permission_service import permission_denied_response, permission_service
from app.users import users_bp

user_repository = UserRepository()

ALLOWED_UPDATE_FIELDS = {"globalRole", "isActive"}
ALLOWED_GLOBAL_ROLES = {"admin", "user"}
ALLOWED_CREATE_FIELDS = {"login", "name", "email", "password", "globalRole"}


def _not_found(name="user"):
    return jsonify({"error": "not_found", "message": f"{name} не найден"}), 404


def _validation_error(details):
    return jsonify({"error": "validation_error", "details": details}), 400


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

    unknown = set(payload) - ALLOWED_UPDATE_FIELDS
    if unknown:
        return _validation_error([{"loc": [k], "msg": "unknown field"} for k in unknown])

    global_role = payload.get("globalRole")
    if global_role is not None and global_role not in ALLOWED_GLOBAL_ROLES:
        return _validation_error([{"loc": ["globalRole"], "msg": "must be 'admin' or 'user'"}])

    is_active = payload.get("isActive")
    if is_active is not None and not isinstance(is_active, bool):
        return _validation_error([{"loc": ["isActive"], "msg": "must be boolean"}])

    updated = user_repository.update(user_id, global_role=global_role, is_active=is_active)
    if updated is None:
        return _not_found()
    return jsonify(domain_to_dto.user(updated).model_dump(by_alias=True))


@users_bp.route("", methods=["POST"])
def create_user(**kwargs):
    if not permission_service.is_global_admin(current_user_id()):
        return permission_denied_response("Создавать пользователей может только администратор")

    payload = request.get_json(silent=True) or {}

    unknown = set(payload) - ALLOWED_CREATE_FIELDS
    if unknown:
        return _validation_error([{"loc": [k], "msg": "unknown field"} for k in unknown])

    login = (payload.get("login") or "").strip()
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip()
    global_role = payload.get("globalRole", "user")

    errors = []
    if not login:
        errors.append({"loc": ["login"], "msg": "required"})
    if not name:
        errors.append({"loc": ["name"], "msg": "required"})
    if not email:
        errors.append({"loc": ["email"], "msg": "required"})
    if global_role not in ALLOWED_GLOBAL_ROLES:
        errors.append({"loc": ["globalRole"], "msg": "must be 'admin' or 'user'"})
    if errors:
        return _validation_error(errors)

    if user_repository.get_by_login(login) is not None:
        return _validation_error([{"loc": ["login"], "msg": "login уже занят"}])

    # Пароль можно передать явно (payload.password) или сгенерировать временный --
    # так же, как это делает seed_initial_users для встроенных admin/user.
    plain_password = (payload.get("password") or "").strip() or secrets.token_urlsafe(9)
    if len(plain_password) < 8:
        return _validation_error([{"loc": ["password"], "msg": "минимум 8 символов"}])

    created = user_repository.create(
        login=login,
        name=name,
        email=email,
        password_hash=generate_password_hash(plain_password),
        global_role=global_role,
    )
    dto = domain_to_dto.user(created).model_dump(by_alias=True)
    dto["temporaryPassword"] = plain_password
    return jsonify(dto), 201


@users_bp.route("/<string:user_id>/reset-password", methods=["POST"])
def reset_password(user_id, **kwargs):
    if not permission_service.is_global_admin(current_user_id()):
        return permission_denied_response("Сбрасывать пароль может только администратор")

    plain_password = secrets.token_urlsafe(9)
    updated = user_repository.set_password_hash(user_id, generate_password_hash(plain_password))
    if updated is None:
        return _not_found()

    dto = domain_to_dto.user(updated).model_dump(by_alias=True)
    dto["temporaryPassword"] = plain_password
    return jsonify(dto)
