"""
Реализация blueprint 'notifications' поверх NotificationRepository (app.repositories).

GET /notifications, POST /notifications (создание due_soon/overdue уведомлений с фронта --
временное решение, см. backend/README.md и Промпт 19), PATCH отметка прочитано/нет,
mark-all-read и DELETE.
"""

from flask import jsonify, request

from app.auth.security import current_user_id
from app.mappers import domain_to_dto
from app.notifications import notifications_bp
from app.repositories import NotificationRepository

notification_repository = NotificationRepository()


def _not_found():
    return jsonify({"error": "not_found", "message": "уведомление не найдено"}), 404


@notifications_bp.route("", methods=["GET"])
def list_notifications(**kwargs):
    user_id = request.args.get("userId") or current_user_id()
    notifications = notification_repository.get_by_user_id(user_id)
    return jsonify([domain_to_dto.notification(n).model_dump(by_alias=True) for n in notifications])


@notifications_bp.route("", methods=["POST"])
def create_notification(**kwargs):
    """Временное решение: due_soon/overdue-уведомления в http-режиме создаются
    фронтом через этот эндпоинт (аналог tasksStore проверки due_date на клиенте).
    Замена на серверный background job -- см. Промпт 19, здесь не реализуется."""
    user_id = current_user_id()
    payload = request.get_json(silent=True) or {}
    notification = notification_repository.create(
        user_id=payload.get("userId", user_id),
        type=payload.get("type"),
        title=payload.get("title"),
        body=payload.get("body", ""),
        task_id=payload.get("taskId"),
        list_id=payload.get("listId"),
        actor_id=payload.get("actorId"),
    )
    return jsonify(domain_to_dto.notification(notification).model_dump(by_alias=True)), 201


@notifications_bp.route("/<string:notification_id>", methods=["PATCH"])
def update_notification(notification_id, **kwargs):
    payload = request.get_json(silent=True) or {}
    patch = {}
    if "read" in payload:
        patch["read"] = payload["read"]
    notification = notification_repository.update(notification_id, patch)
    if notification is None:
        return _not_found()
    return jsonify(domain_to_dto.notification(notification).model_dump(by_alias=True))


@notifications_bp.route("/<string:notification_id>", methods=["DELETE"])
def delete_notification(notification_id, **kwargs):
    deleted = notification_repository.delete(notification_id)
    if not deleted:
        return _not_found()
    return "", 204


@notifications_bp.route("/mark-all-read", methods=["POST"])
def mark_all_read(**kwargs):
    user_id = current_user_id()
    count = notification_repository.mark_all_read(user_id)
    return jsonify({"updated": count})
