"""
Реализация blueprint 'users' поверх UserRepository (app.repositories).
Автентификация -- глобальным guard в app.auth.security (401 для всего
blueprint). PATCH /users/:id доступен только global admin (PermissionService.is_global_admin) --
зеркало frontend-правила UsersView.vue (редактировать роль/активность
другого пользователя может только админ).

Роли пользователя (globalRole): 'admin' | 'manager' | 'user'.
'manager' -- руководитель одного или нескольких отделов/служб сразу (связь
годами -- managerDepartmentIds, через ManagerDepartmentORM). Сам себе руководитель назначать
не может -- назначать globalRole='manager' и managerDepartmentIds также может только admin.

Поле department_id (ссылка на справочник Department) -- отдел, в котором работает
сам сотрудник; не путать с managerDepartmentIds (отделы, которыми он руководит).

Поле is_system -- служебные учётные записи, не отображаемые в списках
назначения исполнителей. GET /api/users отдаёт только реальных
пользователей (is_system=False). Администратор может управлять
флагом isSystem через PATCH /api/users/:id.

POST /users (создание) и POST /users/:id/reset-password -- тоже только global admin.
Пароль (при создании -- заданный явно, при сбросе -- сгенерированный временный)
возвращается в JSON-ответе ОДИН РАЗ, как открытый текст -- аналог поведения
app.auth.seed.seed_initial_users (пароль печатается один раз и не хранится в
открытом виде). Ответственность фронтенда -- показать его администратору сразу
и не сохранять его.

POST/DELETE /users/:id/avatar -- загрузка/сброс аватара. Доступно только global
admin (зеркалит остальные mutating-эндпойнты этого blueprint) -- аватар редактируется
из той же модалки UsersView.vue, что и остальные поля. Файл сохраняется
на диск через app.uploads.routes.avatars_dir(), а users.avatar_url хранит только
относительный путь вида /api/uploads/avatars/<filename> (см. HttpUserRepository.js).
"""

import os
import secrets

from flask import jsonify, request
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename

from app.auth.security import current_user_id
from app.mappers import domain_to_dto
from app.repositories import DepartmentRepository, UserRepository
from app.repositories.user_repository import DuplicateEmailError, DuplicateLoginError
from app.services.permission_service import permission_denied_response, permission_service
from app.uploads.routes import avatars_dir
from app.users import users_bp

user_repository = UserRepository()
department_repository = DepartmentRepository()

ALLOWED_UPDATE_FIELDS = {
    "globalRole", "isActive", "isSystem", "name", "email", "position", "department",
    "departmentId", "managerDepartmentIds",
}
ALLOWED_GLOBAL_ROLES = {"admin", "manager", "user"}
ALLOWED_CREATE_FIELDS = {
    "login", "name", "email", "password", "globalRole", "position", "department",
    "departmentId", "managerDepartmentIds",
}
ALLOWED_AVATAR_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_AVATAR_SIZE_BYTES = 5 * 1024 * 1024


def _not_found(name="user"):
    return jsonify({"error": "not_found", "message": f"{name} не найден"}), 404


def _validation_error(details):
    return jsonify({"error": "validation_error", "details": details}), 400


def _validate_department_id(department_id):
    if department_id is None:
        return None
    if department_repository.get_by_id(department_id) is None:
        return _validation_error([{"loc": ["departmentId"], "msg": "отдел не найден"}])
    return None


def _validate_manager_department_ids(manager_department_ids):
    if manager_department_ids is None:
        return None
    if not isinstance(manager_department_ids, list) or not all(isinstance(x, str) for x in manager_department_ids):
        return _validation_error([{"loc": ["managerDepartmentIds"], "msg": "ожидается список строк"}])
    for department_id in manager_department_ids:
        if department_repository.get_by_id(department_id) is None:
            return _validation_error([{"loc": ["managerDepartmentIds"], "msg": f"отдел {department_id} не найден"}])
    return None


@users_bp.route("", methods=["GET"])
def list_users(**kwargs):
    if permission_service.is_global_admin(current_user_id()):
        # Админ видит всех пользователей (включая служебных), но системных --
        # отфильтрованных (им не нужно назначать задачи).
        users = [u for u in user_repository.get_all() if not u.is_system]
    else:
        users = user_repository.get_all_active()
    return jsonify([domain_to_dto.user(u).model_dump(by_alias=True) for u in users])


@users_bp.route("/admin/all", methods=["GET"])
def list_all_users_admin(**kwargs):
    """Только для admin: полный список включая служебных пользователей.
    Используется модалькой администрирования пользователей — для просмотра и
    управления служебными учётными записями.
    """
    if not permission_service.is_global_admin(current_user_id()):
        return permission_denied_response("Доступ только для администратора")
    users = user_repository.get_all()
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
        return _validation_error([{"loc": ["globalRole"], "msg": "must be 'admin', 'manager' or 'user'"}])

    is_active = payload.get("isActive")
    if is_active is not None and not isinstance(is_active, bool):
        return _validation_error([{"loc": ["isActive"], "msg": "must be boolean"}])

    is_system = payload.get("isSystem")
    if is_system is not None and not isinstance(is_system, bool):
        return _validation_error([{"loc": ["isSystem"], "msg": "must be boolean"}])

    name = payload.get("name")
    if name is not None and not str(name).strip():
        return _validation_error([{"loc": ["name"], "msg": "не может быть пустым"}])

    email = payload.get("email")
    if email is not None and not str(email).strip():
        return _validation_error([{"loc": ["email"], "msg": "не может быть пустым"}])

    position = payload.get("position")
    department = payload.get("department")

    department_id = payload.get("departmentId")
    clear_department_id = "departmentId" in payload and department_id is None
    error = _validate_department_id(department_id)
    if error is not None:
        return error

    manager_department_ids = payload.get("managerDepartmentIds")
    error = _validate_manager_department_ids(manager_department_ids)
    if error is not None:
        return error

    try:
        updated = user_repository.update(
            user_id,
            global_role=global_role,
            is_active=is_active,
            is_system=is_system,
            name=name.strip() if name is not None else None,
            email=email.strip() if email is not None else None,
            position=position,
            department=department,
            department_id=department_id,
            clear_department_id=clear_department_id,
            managed_department_ids=manager_department_ids,
        )
    except DuplicateEmailError:
        return _validation_error([{"loc": ["email"], "msg": "email уже занят другим пользователем"}])

    if updated is None:
        return _not_found()
    return jsonify(domain_to_dto.user(updated).model_dump(by_alias=True))


@users_bp.route("/<string:user_id>", methods=["DELETE"])
def delete_user(user_id, **kwargs):
    if not permission_service.is_global_admin(current_user_id()):
        return permission_denied_response("Удалять пользователей может только администратор")

    if user_id == current_user_id():
        return permission_denied_response("Нельзя удалить собственную учётную запись")

    deleted = user_repository.delete(user_id)
    if not deleted:
        return _not_found()
    return "", 204


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
    position = payload.get("position")
    department = payload.get("department")
    department_id = payload.get("departmentId")
    manager_department_ids = payload.get("managerDepartmentIds")

    errors = []
    if not login:
        errors.append({"loc": ["login"], "msg": "required"})
    if not name:
        errors.append({"loc": ["name"], "msg": "required"})
    if not email:
        errors.append({"loc": ["email"], "msg": "required"})
    if global_role not in ALLOWED_GLOBAL_ROLES:
        errors.append({"loc": ["globalRole"], "msg": "must be 'admin', 'manager' or 'user'"})
    if errors:
        return _validation_error(errors)

    if user_repository.get_by_login(login) is not None:
        return _validation_error([{"loc": ["login"], "msg": "login уже занят"}])

    if user_repository.get_by_email(email) is not None:
        return _validation_error([{"loc": ["email"], "msg": "email уже занят"}])

    error = _validate_department_id(department_id)
    if error is not None:
        return error

    error = _validate_manager_department_ids(manager_department_ids)
    if error is not None:
        return error

    plain_password = (payload.get("password") or "").strip() or secrets.token_urlsafe(9)
    if len(plain_password) < 8:
        return _validation_error([{"loc": ["password"], "msg": "минимум 8 символов"}])

    try:
        created = user_repository.create(
            login=login,
            name=name,
            email=email,
            password_hash=generate_password_hash(plain_password),
            global_role=global_role,
            position=position,
            department=department,
            department_id=department_id,
        )
    except DuplicateLoginError:
        return _validation_error([{"loc": ["login"], "msg": "login уже занят"}])
    except DuplicateEmailError:
        return _validation_error([{"loc": ["email"], "msg": "email уже занят"}])

    if manager_department_ids is not None:
        try:
            created = user_repository.update(created.id, managed_department_ids=manager_department_ids)
        except DuplicateEmailError:
            pass

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


@users_bp.route("/<string:user_id>/avatar", methods=["POST"])
def upload_avatar(user_id, **kwargs):
    if not permission_service.is_global_admin(current_user_id()):
        return permission_denied_response("Изменять аватар может только администратор")

    if user_repository.get_by_id(user_id) is None:
        return _not_found()

    uploaded_file = request.files.get("avatar")
    if uploaded_file is None or not uploaded_file.filename:
        return _validation_error([{"loc": ["avatar"], "msg": "файл не передан"}])

    extension = uploaded_file.filename.rsplit(".", 1)[-1].lower() if "." in uploaded_file.filename else ""
    if extension not in ALLOWED_AVATAR_EXTENSIONS:
        return _validation_error([{"loc": ["avatar"], "msg": "допустимые форматы: png, jpg, jpeg, gif, webp"}])

    uploaded_file.stream.seek(0, os.SEEK_END)
    size_bytes = uploaded_file.stream.tell()
    uploaded_file.stream.seek(0)
    if size_bytes > MAX_AVATAR_SIZE_BYTES:
        return _validation_error([{"loc": ["avatar"], "msg": "файл больше 5 МБ"}])

    filename = secure_filename(f"{user_id}-{secrets.token_hex(6)}.{extension}")
    uploaded_file.save(os.path.join(avatars_dir(), filename))

    avatar_url = f"/api/uploads/avatars/{filename}"
    updated = user_repository.set_avatar_url(user_id, avatar_url)
    if updated is None:
        return _not_found()
    return jsonify(domain_to_dto.user(updated).model_dump(by_alias=True))


@users_bp.route("/<string:user_id>/avatar", methods=["DELETE"])
def delete_avatar(user_id, **kwargs):
    if not permission_service.is_global_admin(current_user_id()):
        return permission_denied_response("Изменять аватар может только администратор")

    updated = user_repository.reset_avatar_url(user_id)
    if updated is None:
        return _not_found()
    return jsonify(domain_to_dto.user(updated).model_dump(by_alias=True))
