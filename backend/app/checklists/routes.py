"""
Реализация blueprint 'checklists' (/api/checklist-items). Права проверяются
по родительской задаче (can_edit_task) -- сами checklist-items не имеют own
прав доступа.
"""

from flask import jsonify, request

from app.auth.security import current_user_id
from app.checklists import checklists_bp
from app.mappers import domain_to_dto
from app.repositories import ChecklistItemRepository, TaskRepository
from app.services.permission_service import permission_denied_response, permission_service

checklist_repository = ChecklistItemRepository()
task_repository = TaskRepository()


def _not_found():
    return jsonify({"error": "not_found", "message": "Пункт чек-листа не найден"}), 404


def _guard(item_id):
    item = checklist_repository.get_by_id(item_id)
    if item is None:
        return None, _not_found()
    task = task_repository.get_by_id(item.task_id)
    if task is None:
        return None, _not_found()
    if not permission_service.can_edit_task(task, current_user_id()):
        return None, permission_denied_response("Недостаточно прав для редактирования задачи")
    return item, None


@checklists_bp.route("/<string:item_id>", methods=["PATCH"])
def update_checklist_item(item_id, **kwargs):
    item, error = _guard(item_id)
    if error:
        return error

    payload = request.get_json(silent=True) or {}
    patch = {}
    if "title" in payload:
        patch["title"] = payload["title"]
    if "done" in payload:
        patch["done"] = payload["done"]
    if "order" in payload:
        patch["order"] = payload["order"]
    if "recurrenceScope" in payload:
        patch["recurrence_scope"] = payload["recurrenceScope"]

    updated = checklist_repository.update(item_id, patch)
    task_repository.touch_activity(item.task_id)
    return jsonify(domain_to_dto.checklist_item(updated).model_dump(by_alias=True))


@checklists_bp.route("/<string:item_id>", methods=["DELETE"])
def delete_checklist_item(item_id, **kwargs):
    item, error = _guard(item_id)
    if error:
        return error

    checklist_repository.delete(item_id)
    task_repository.touch_activity(item.task_id)
    return "", 204
