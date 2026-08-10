"""
Заглушки роутов blueprint 'lists'. Бизнес-логика не реализована —
каждый эндпоинт возвращает 501 Not Implemented, чтобы зафиксировать
URL-контракт под уже существующий frontend apiClient (src/repositories/http/apiClient.js)
до реализации соответствующих repositories/services на backend.
"""

from flask import jsonify

from app.lists import lists_bp


def _not_implemented(name):
    return jsonify({"message": f"{name} not implemented"}), 501


@lists_bp.route("", methods=["GET"])
def list_lists(**kwargs):
    return _not_implemented("list_lists")

@lists_bp.route("", methods=["POST"])
def create_list(**kwargs):
    return _not_implemented("create_list")

@lists_bp.route("/<string:list_id>", methods=["GET"])
def get_list(**kwargs):
    return _not_implemented("get_list")

@lists_bp.route("/<string:list_id>", methods=["PATCH"])
def update_list(**kwargs):
    return _not_implemented("update_list")

@lists_bp.route("/<string:list_id>", methods=["DELETE"])
def delete_list(**kwargs):
    return _not_implemented("delete_list")

@lists_bp.route("/<string:list_id>/memberships", methods=["GET"])
def list_memberships(**kwargs):
    return _not_implemented("list_memberships")

@lists_bp.route("/<string:list_id>/memberships", methods=["POST"])
def add_membership(**kwargs):
    return _not_implemented("add_membership")

@lists_bp.route("/<string:list_id>/memberships/<string:user_id>", methods=["DELETE"])
def remove_membership(**kwargs):
    return _not_implemented("remove_membership")
