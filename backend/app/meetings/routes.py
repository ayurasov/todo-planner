"""
Заглушки роутов blueprint 'meetings'. Бизнес-логика не реализована —
каждый эндпоинт возвращает 501 Not Implemented, чтобы зафиксировать
URL-контракт под уже существующий frontend apiClient (src/repositories/http/apiClient.js)
до реализации соответствующих repositories/services на backend.
"""

from flask import jsonify

from app.meetings import meetings_bp


def _not_implemented(name):
    return jsonify({"message": f"{name} not implemented"}), 501


@meetings_bp.route("", methods=["GET"])
def list_meetings(**kwargs):
    return _not_implemented("list_meetings")

@meetings_bp.route("", methods=["POST"])
def create_meeting(**kwargs):
    return _not_implemented("create_meeting")

@meetings_bp.route("/<string:meeting_id>", methods=["GET"])
def get_meeting(**kwargs):
    return _not_implemented("get_meeting")

@meetings_bp.route("/<string:meeting_id>", methods=["PATCH"])
def update_meeting(**kwargs):
    return _not_implemented("update_meeting")

@meetings_bp.route("/<string:meeting_id>", methods=["DELETE"])
def delete_meeting(**kwargs):
    return _not_implemented("delete_meeting")

@meetings_bp.route("/<string:meeting_id>/occurrences", methods=["GET"])
def list_meeting_occurrences(**kwargs):
    return _not_implemented("list_meeting_occurrences")
