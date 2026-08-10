"""
Заглушки роутов blueprint 'comments'. Бизнес-логика не реализована —
каждый эндпоинт возвращает 501 Not Implemented, чтобы зафиксировать
URL-контракт под уже существующий frontend apiClient (src/repositories/http/apiClient.js)
до реализации соответствующих repositories/services на backend.
"""

from flask import jsonify

from app.comments import comments_bp


def _not_implemented(name):
    return jsonify({"message": f"{name} not implemented"}), 501


@comments_bp.route("/<string:comment_id>", methods=["PATCH"])
def update_comment(**kwargs):
    return _not_implemented("update_comment")

@comments_bp.route("/<string:comment_id>", methods=["DELETE"])
def delete_comment(**kwargs):
    return _not_implemented("delete_comment")
