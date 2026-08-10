"""
Заглушки роутов blueprint 'saved_views'. Бизнес-логика не реализована —
каждый эндпоинт возвращает 501 Not Implemented, чтобы зафиксировать
URL-контракт под уже существующий frontend apiClient (src/repositories/http/apiClient.js)
до реализации соответствующих repositories/services на backend.
"""

from flask import jsonify

from app.saved_views import saved_views_bp


def _not_implemented(name):
    return jsonify({"message": f"{name} not implemented"}), 501


@saved_views_bp.route("", methods=["GET"])
def list_saved_views(**kwargs):
    return _not_implemented("list_saved_views")

@saved_views_bp.route("", methods=["POST"])
def create_saved_view(**kwargs):
    return _not_implemented("create_saved_view")

@saved_views_bp.route("/<string:view_id>", methods=["PATCH"])
def update_saved_view(**kwargs):
    return _not_implemented("update_saved_view")

@saved_views_bp.route("/<string:view_id>", methods=["DELETE"])
def delete_saved_view(**kwargs):
    return _not_implemented("delete_saved_view")
