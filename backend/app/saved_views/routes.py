"""
Реализация blueprint 'saved_views' поверх SavedViewRepository (app.repositories).
Сохранённые виды всегда привязаны к user_id текущего авторизованного
пользователя -- лишний ресурс, не разделяется между членами команды.
"""

from flask import jsonify, request

from app.auth.security import current_user_id
from app.mappers import domain_to_dto
from app.repositories import SavedViewRepository
from app.saved_views import saved_views_bp

saved_view_repository = SavedViewRepository()


def _not_found():
    return jsonify({"error": "not_found", "message": "сохранённый вид не найден"}), 404


def _validation_error(details):
    return jsonify({"error": "validation_error", "details": details}), 400


def _permission_denied():
    return jsonify({"error": "permission_denied", "message": "вид принадлежит другому пользователю"}), 403


@saved_views_bp.route("", methods=["GET"])
def list_saved_views(**kwargs):
    user_id = request.args.get("userId") or current_user_id()
    views = saved_view_repository.get_by_user_id(user_id)
    return jsonify([domain_to_dto.saved_view(v).model_dump(by_alias=True) for v in views])


@saved_views_bp.route("", methods=["POST"])
def create_saved_view(**kwargs):
    user_id = current_user_id()
    payload = request.get_json(silent=True) or {}
    name = payload.get("name")
    if not name:
        return _validation_error([{"loc": ["name"], "msg": "required"}])

    view = saved_view_repository.create(
        user_id=user_id,
        name=name,
        filters=payload.get("filters", {}),
        sort=payload.get("sort", {"field": "score", "dir": "desc"}),
        group_by=payload.get("groupBy"),
        pinned=payload.get("pinned", False),
    )
    return jsonify(domain_to_dto.saved_view(view).model_dump(by_alias=True)), 201


@saved_views_bp.route("/<string:view_id>", methods=["PATCH"])
def update_saved_view(view_id, **kwargs):
    user_id = current_user_id()
    existing = saved_view_repository.get_by_id(view_id)
    if existing is None:
        return _not_found()
    if existing.user_id != user_id:
        return _permission_denied()

    payload = request.get_json(silent=True) or {}
    field_map = {"name": "name", "filters": "filters", "sort": "sort", "groupBy": "group_by", "pinned": "pinned"}
    patch = {snake: payload[camel] for camel, snake in field_map.items() if camel in payload}

    view = saved_view_repository.update(view_id, patch)
    return jsonify(domain_to_dto.saved_view(view).model_dump(by_alias=True))


@saved_views_bp.route("/<string:view_id>", methods=["DELETE"])
def delete_saved_view(view_id, **kwargs):
    user_id = current_user_id()
    existing = saved_view_repository.get_by_id(view_id)
    if existing is None:
        return _not_found()
    if existing.user_id != user_id:
        return _permission_denied()

    saved_view_repository.delete(view_id)
    return "", 204
