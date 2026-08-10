"""
Заглушки роутов blueprint 'tasks'. Бизнес-логика не реализована —
каждый эндпоинт возвращает 501 Not Implemented, чтобы зафиксировать
URL-контракт под уже существующий frontend apiClient (src/repositories/http/apiClient.js)
до реализации соответствующих repositories/services на backend.
"""

from flask import jsonify

from app.tasks import tasks_bp


def _not_implemented(name):
    return jsonify({"message": f"{name} not implemented"}), 501


@tasks_bp.route("", methods=["GET"])
def list_tasks(**kwargs):
    return _not_implemented("list_tasks")

@tasks_bp.route("", methods=["POST"])
def create_task(**kwargs):
    return _not_implemented("create_task")

@tasks_bp.route("/<string:task_id>", methods=["GET"])
def get_task(**kwargs):
    return _not_implemented("get_task")

@tasks_bp.route("/<string:task_id>", methods=["PATCH"])
def update_task(**kwargs):
    return _not_implemented("update_task")

@tasks_bp.route("/<string:task_id>", methods=["DELETE"])
def delete_task(**kwargs):
    return _not_implemented("delete_task")

@tasks_bp.route("/<string:task_id>/checklist-items", methods=["GET"])
def list_task_checklist_items(**kwargs):
    return _not_implemented("list_task_checklist_items")

@tasks_bp.route("/<string:task_id>/checklist-items", methods=["POST"])
def create_task_checklist_item(**kwargs):
    return _not_implemented("create_task_checklist_item")

@tasks_bp.route("/<string:task_id>/notes", methods=["GET"])
def get_task_note(**kwargs):
    return _not_implemented("get_task_note")

@tasks_bp.route("/<string:task_id>/comments", methods=["GET"])
def list_task_comments(**kwargs):
    return _not_implemented("list_task_comments")

@tasks_bp.route("/<string:task_id>/comments", methods=["POST"])
def create_task_comment(**kwargs):
    return _not_implemented("create_task_comment")

@tasks_bp.route("/<string:task_id>/attachments", methods=["GET"])
def list_task_attachments(**kwargs):
    return _not_implemented("list_task_attachments")

@tasks_bp.route("/<string:task_id>/attachments", methods=["POST"])
def upload_task_attachment(**kwargs):
    return _not_implemented("upload_task_attachment")

@tasks_bp.route("/<string:task_id>/history", methods=["GET"])
def get_task_history(**kwargs):
    return _not_implemented("get_task_history")
