"""
Реализация blueprint 'comments' (/api/comments). Редактировать комментарий
может только автор; удалять -- автор или любой, кто имеет can_edit_task
на родительской задаче (owner/editor/assignee-владелец).
"""

from flask import jsonify, request

from app.auth.security import current_user_id
from app.comments import comments_bp
from app.mappers import domain_to_dto
from app.repositories import CommentRepository, TaskRepository
from app.services.permission_service import permission_denied_response, permission_service

comment_repository = CommentRepository()
task_repository = TaskRepository()


def _not_found():
    return jsonify({"error": "not_found", "message": "комментарий не найден"}), 404


@comments_bp.route("/<string:comment_id>", methods=["PATCH"])
def update_comment(comment_id, **kwargs):
    comment = comment_repository.get_by_id(comment_id)
    if comment is None:
        return _not_found()

    user_id = current_user_id()
    if comment.author_id != user_id and not permission_service.is_global_admin(user_id):
        return permission_denied_response("Редактировать комментарий может только автор")

    payload = request.get_json(silent=True) or {}
    updated = comment_repository.update(
        comment_id, text=payload.get("text"), mentions=payload.get("mentions"),
    )
    task_repository.touch_activity(comment.task_id)
    return jsonify(domain_to_dto.comment(updated).model_dump(by_alias=True))


@comments_bp.route("/<string:comment_id>", methods=["DELETE"])
def delete_comment(comment_id, **kwargs):
    comment = comment_repository.get_by_id(comment_id)
    if comment is None:
        return _not_found()

    user_id = current_user_id()
    task = task_repository.get_by_id(comment.task_id)
    can_delete = (
        comment.author_id == user_id
        or permission_service.is_global_admin(user_id)
        or (task is not None and permission_service.can_edit_task(task, user_id))
    )
    if not can_delete:
        return permission_denied_response("Недостаточно прав для удаления комментария")

    comment_repository.delete(comment_id)
    task_repository.touch_activity(comment.task_id)
    return "", 204
