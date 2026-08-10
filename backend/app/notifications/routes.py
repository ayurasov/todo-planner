"""
Заглушки роутов blueprint 'notifications'. Бизнес-логика не реализована —
каждый эндпоинт возвращает 501 Not Implemented, чтобы зафиксировать
URL-контракт под уже существующий frontend apiClient (src/repositories/http/apiClient.js)
до реализации соответствующих repositories/services на backend.
"""

from flask import jsonify

from app.notifications import notifications_bp


def _not_implemented(name):
    return jsonify({"message": f"{name} not implemented"}), 501


@notifications_bp.route("", methods=["GET"])
def list_notifications(**kwargs):
    return _not_implemented("list_notifications")

@notifications_bp.route("/<string:notification_id>", methods=["PATCH"])
def update_notification(**kwargs):
    return _not_implemented("update_notification")

@notifications_bp.route("/mark-all-read", methods=["POST"])
def mark_all_read(**kwargs):
    return _not_implemented("mark_all_read")
