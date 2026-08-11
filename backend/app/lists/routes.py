"""
Реализация blueprint 'lists' поверх ListRepository (app.repositories).

Доступконтроль:
  - GET /lists            -- только доступные текущему пользователю списки
                             (permission_service.get_accessible_list_ids), все -- для global admin.
  - POST /lists           -- создаёт список, owner = текущий пользователь.
  - GET/PATCH/DELETE /lists/:id -- @require_list_permission (can_view_list / can_view_list / can_delete_list).
  - GET/POST /lists/:id/memberships, DELETE .../memberships/:userId --
    @require_list_permission("can_manage_members") для мутаций; GET доступен любому,
    кто видит список (can_view_list) -- без этого ListSettingsModal.vue не смогла
    бы показать список участников обычному editor/viewer.
"""

from flask import jsonify, request

from app.auth.security import current_user_id
from app.mappers import domain_to_dto
from app.repositories import ListRepository
from app.services.permission_service import (
    permission_denied_response,
    permission_service,
    require_list_permission,
)
from app.lists import lists_bp

list_repository = ListRepository()

ALLOWED_ROLES = {"owner", "editor", "assignee", "viewer"}


def _not_found(name="list"):
    return jsonify({"error": "not_found", "message": f"{name} не найден"}), 404


def _validation_error(details):
    return jsonify({"error": "validation_error", "details": details}), 400


@lists_bp.route("", methods=["GET"])
def list_lists(**kwargs):
    lists = list_repository.get_accessible(current_user_id())
    return jsonify([domain_to_dto.todo_list(l).model_dump(by_alias=True) for l in lists])


@lists_bp.route("", methods=["POST"])
def create_list(**kwargs):
    payload = request.get_json(silent=True) or {}
    title = payload.get("title")
    if not title:
        return _validation_error([{"loc": ["title"], "msg": "required"}])

    created = list_repository.create(
        title=title,
        description=payload.get("description", ""),
        color=payload.get("color", "#4f7cff"),
        is_shared=payload.get("isShared", False),
        default_view=payload.get("defaultView", "list"),
        settings=payload.get("settings", {}),
        owner_id=current_user_id(),
    )
    return jsonify(domain_to_dto.todo_list(created).model_dump(by_alias=True)), 201


@lists_bp.route("/<string:list_id>", methods=["GET"])
@require_list_permission("can_view_list")
def get_list(list_id, **kwargs):
    todo_list = list_repository.get_by_id(list_id)
    if todo_list is None:
        return _not_found()
    return jsonify(domain_to_dto.todo_list(todo_list).model_dump(by_alias=True))


@lists_bp.route("/<string:list_id>", methods=["PATCH"])
@require_list_permission("can_view_list")
def update_list(list_id, **kwargs):
    # редактировать настройки/метаданные списка могут owner/editor --
    # то же правило, что и для can_create_task (ср. src/services/PermissionService.js).
    if not permission_service.can_create_task(list_id, current_user_id()):
        return permission_denied_response("Недостаточно прав для редактирования списка")

    payload = request.get_json(silent=True) or {}
    patch = {}
    if "title" in payload:
        patch["title"] = payload["title"]
    if "description" in payload:
        patch["description"] = payload["description"]
    if "color" in payload:
        patch["color"] = payload["color"]
    if "isShared" in payload:
        patch["is_shared"] = payload["isShared"]
    if "defaultView" in payload:
        patch["default_view"] = payload["defaultView"]
    if "settings" in payload:
        patch["settings"] = payload["settings"]
    if "archived" in payload:
        patch["archived"] = payload["archived"]
    if "order" in payload:
        patch["order"] = payload["order"]

    updated = list_repository.update(list_id, patch)
    if updated is None:
        return _not_found()
    return jsonify(domain_to_dto.todo_list(updated).model_dump(by_alias=True))


@lists_bp.route("/<string:list_id>", methods=["DELETE"])
@require_list_permission("can_delete_list")
def delete_list(list_id, **kwargs):
    deleted = list_repository.delete(list_id)
    if not deleted:
        return _not_found()
    return "", 204


@lists_bp.route("/<string:list_id>/memberships", methods=["GET"])
@require_list_permission("can_view_list")
def list_memberships(list_id, **kwargs):
    members = list_repository.get_members(list_id)
    return jsonify([domain_to_dto.list_membership(m).model_dump(by_alias=True) for m in members])


@lists_bp.route("/<string:list_id>/memberships", methods=["POST"])
@require_list_permission("can_manage_members")
def add_membership(list_id, **kwargs):
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("userId")
    role = payload.get("role")
    if not user_id or role not in ALLOWED_ROLES:
        return _validation_error([{"loc": ["userId/role"], "msg": "userId required, role must be one of owner/editor/assignee/viewer"}])

    membership = list_repository.add_or_update_member(list_id, user_id, role)
    return jsonify(domain_to_dto.list_membership(membership).model_dump(by_alias=True)), 201


@lists_bp.route("/<string:list_id>/memberships/<string:user_id>", methods=["DELETE"])
@require_list_permission("can_manage_members")
def remove_membership(list_id, user_id, **kwargs):
    removed = list_repository.remove_member(list_id, user_id)
    if not removed:
        return _not_found("membership")
    return "", 204
