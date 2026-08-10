"""
Заглушки роутов blueprint 'auth'. Бизнес-логика не реализована —
каждый эндпоинт возвращает 501 Not Implemented, чтобы зафиксировать
URL-контракт под уже существующий frontend apiClient (src/repositories/http/apiClient.js)
до реализации соответствующих repositories/services на backend.
"""

from flask import jsonify

from app.auth import auth_bp


def _not_implemented(name):
    return jsonify({"message": f"{name} not implemented"}), 501


@auth_bp.route("/login", methods=["POST"])
def login(**kwargs):
    return _not_implemented("login")

@auth_bp.route("/logout", methods=["POST"])
def logout(**kwargs):
    return _not_implemented("logout")

@auth_bp.route("/me", methods=["GET"])
def get_current_user(**kwargs):
    return _not_implemented("get_current_user")

@auth_bp.route("/csrf-token", methods=["GET"])
def get_csrf_token(**kwargs):
    return _not_implemented("get_csrf_token")
