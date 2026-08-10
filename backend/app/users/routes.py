"""
Заглушки роутов blueprint 'users'. Бизнес-логика не реализована —
каждый эндпоинт возвращает 501 Not Implemented, чтобы зафиксировать
URL-контракт под уже существующий frontend apiClient (src/repositories/http/apiClient.js)
до реализации соответствующих repositories/services на backend.
"""

from flask import jsonify

from app.users import users_bp


def _not_implemented(name):
    return jsonify({"message": f"{name} not implemented"}), 501


@users_bp.route("", methods=["GET"])
def list_users(**kwargs):
    return _not_implemented("list_users")

@users_bp.route("/<string:user_id>", methods=["GET"])
def get_user(**kwargs):
    return _not_implemented("get_user")

@users_bp.route("/<string:user_id>", methods=["PATCH"])
def update_user(**kwargs):
    return _not_implemented("update_user")
