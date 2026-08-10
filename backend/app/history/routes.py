"""
Заглушки роутов blueprint 'history'. Бизнес-логика не реализована —
каждый эндпоинт возвращает 501 Not Implemented, чтобы зафиксировать
URL-контракт под уже существующий frontend apiClient (src/repositories/http/apiClient.js)
до реализации соответствующих repositories/services на backend.
"""

from flask import jsonify

from app.history import history_bp


def _not_implemented(name):
    return jsonify({"message": f"{name} not implemented"}), 501


@history_bp.route("", methods=["GET"])
def list_history_entries(**kwargs):
    return _not_implemented("list_history_entries")

@history_bp.route("/<string:entry_id>", methods=["GET"])
def get_history_entry(**kwargs):
    return _not_implemented("get_history_entry")
