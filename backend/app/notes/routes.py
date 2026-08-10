"""
Заглушки роутов blueprint 'notes'. Бизнес-логика не реализована —
каждый эндпоинт возвращает 501 Not Implemented, чтобы зафиксировать
URL-контракт под уже существующий frontend apiClient (src/repositories/http/apiClient.js)
до реализации соответствующих repositories/services на backend.
"""

from flask import jsonify

from app.notes import notes_bp


def _not_implemented(name):
    return jsonify({"message": f"{name} not implemented"}), 501


@notes_bp.route("/<string:note_id>", methods=["PATCH"])
def update_note(**kwargs):
    return _not_implemented("update_note")
