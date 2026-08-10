"""
Заглушки роутов blueprint 'checklists'. Бизнес-логика не реализована —
каждый эндпоинт возвращает 501 Not Implemented, чтобы зафиксировать
URL-контракт под уже существующий frontend apiClient (src/repositories/http/apiClient.js)
до реализации соответствующих repositories/services на backend.
"""

from flask import jsonify

from app.checklists import checklists_bp


def _not_implemented(name):
    return jsonify({"message": f"{name} not implemented"}), 501


@checklists_bp.route("/<string:item_id>", methods=["PATCH"])
def update_checklist_item(**kwargs):
    return _not_implemented("update_checklist_item")

@checklists_bp.route("/<string:item_id>", methods=["DELETE"])
def delete_checklist_item(**kwargs):
    return _not_implemented("delete_checklist_item")
