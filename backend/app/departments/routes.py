"""
Реализация blueprint 'departments' поверх DepartmentRepository (app.repositories).

Доступконтроль:
  - GET /departments -- виден любому автентицированному пользователю (справочник
    нужен, например, в селекторах адресата/руководителя при создании задач/встреч).
  - POST/PATCH/DELETE /departments -- только global admin (настраивает справочник).
  - GET /departments/:id/managers -- список руководителей отдела (через manager_departments).
  - PUT /departments/:id/managers -- задать полный список руководителей отдела -- только global admin.
    Руководитель может быть назначен ответственным за несколько отделов/служб одновременно --
    поэтому этот эндпоинт принимает массив userIds (а не одно значение).
"""

from flask import jsonify, request

from app.auth.security import current_user_id
from app.departments import departments_bp
from app.mappers import domain_to_dto
from app.repositories import DepartmentRepository
from app.services.permission_service import permission_denied_response, permission_service

department_repository = DepartmentRepository()


def _not_found():
    return jsonify({"error": "not_found", "message": "отдел не найден"}), 404


def _validation_error(details):
    return jsonify({"error": "validation_error", "details": details}), 400


@departments_bp.route("", methods=["GET"])
def list_departments(**kwargs):
    departments = department_repository.get_all()
    return jsonify([domain_to_dto.department(d).model_dump(by_alias=True) for d in departments])


@departments_bp.route("", methods=["POST"])
def create_department(**kwargs):
    if not permission_service.is_global_admin(current_user_id()):
        return permission_denied_response("Создавать отделы может только администратор")

    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    if not name:
        return _validation_error([{"loc": ["name"], "msg": "required"}])
    if department_repository.get_by_name(name) is not None:
        return _validation_error([{"loc": ["name"], "msg": "отдел с таким именем уже существует"}])

    created = department_repository.create(name=name)
    return jsonify(domain_to_dto.department(created).model_dump(by_alias=True)), 201


@departments_bp.route("/<string:department_id>", methods=["PATCH"])
def update_department(department_id, **kwargs):
    if not permission_service.is_global_admin(current_user_id()):
        return permission_denied_response("Редактировать отделы может только администратор")

    payload = request.get_json(silent=True) or {}
    name = payload.get("name")
    if name is not None:
        name = name.strip()
        if not name:
            return _validation_error([{"loc": ["name"], "msg": "не может быть пустым"}])
        existing = department_repository.get_by_name(name)
        if existing is not None and existing.id != department_id:
            return _validation_error([{"loc": ["name"], "msg": "отдел с таким именем уже существует"}])

    updated = department_repository.update(department_id, name=name)
    if updated is None:
        return _not_found()
    return jsonify(domain_to_dto.department(updated).model_dump(by_alias=True))


@departments_bp.route("/<string:department_id>", methods=["DELETE"])
def delete_department(department_id, **kwargs):
    if not permission_service.is_global_admin(current_user_id()):
        return permission_denied_response("Удалять отделы может только администратор")

    deleted = department_repository.delete(department_id)
    if not deleted:
        return _not_found()
    return "", 204


@departments_bp.route("/<string:department_id>/managers", methods=["GET"])
def list_department_managers(department_id, **kwargs):
    if department_repository.get_by_id(department_id) is None:
        return _not_found()
    manager_ids = department_repository.get_manager_ids(department_id)
    return jsonify(manager_ids)


@departments_bp.route("/<string:department_id>/managers", methods=["PUT"])
def set_department_managers(department_id, **kwargs):
    if not permission_service.is_global_admin(current_user_id()):
        return permission_denied_response("Заново руководителей может только администратор")

    if department_repository.get_by_id(department_id) is None:
        return _not_found()

    payload = request.get_json(silent=True) or {}
    user_ids = payload.get("userIds")
    if not isinstance(user_ids, list) or not all(isinstance(u, str) for u in user_ids):
        return _validation_error([{"loc": ["userIds"], "msg": "ожидается список строк"}])

    manager_ids = department_repository.set_managers(department_id, user_ids)
    return jsonify(manager_ids)
