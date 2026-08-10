"""
Заглушки роутов blueprint 'recurrence'. Бизнес-логика не реализована —
каждый эндпоинт возвращает 501 Not Implemented, чтобы зафиксировать
URL-контракт под уже существующий frontend apiClient (src/repositories/http/apiClient.js)
до реализации соответствующих repositories/services на backend.
"""

from flask import jsonify

from app.recurrence import recurrence_bp


def _not_implemented(name):
    return jsonify({"message": f"{name} not implemented"}), 501


@recurrence_bp.route("", methods=["GET"])
def list_recurrence_templates(**kwargs):
    return _not_implemented("list_recurrence_templates")

@recurrence_bp.route("", methods=["POST"])
def create_recurrence_template(**kwargs):
    return _not_implemented("create_recurrence_template")

@recurrence_bp.route("/<string:template_id>", methods=["GET"])
def get_recurrence_template(**kwargs):
    return _not_implemented("get_recurrence_template")

@recurrence_bp.route("/<string:template_id>", methods=["PATCH"])
def update_recurrence_template(**kwargs):
    return _not_implemented("update_recurrence_template")

@recurrence_bp.route("/<string:template_id>", methods=["DELETE"])
def delete_recurrence_template(**kwargs):
    return _not_implemented("delete_recurrence_template")
