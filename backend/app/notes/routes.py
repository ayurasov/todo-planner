"""
Реализация blueprint 'notes' (/api/notes). Права проверяются по родительской
задаче (can_edit_task).
"""

from flask import jsonify, request

from app.auth.security import current_user_id
from app.mappers import domain_to_dto
from app.notes import notes_bp
from app.repositories import NoteRepository, TaskRepository
from app.services.permission_service import permission_denied_response, permission_service

note_repository = NoteRepository()
task_repository = TaskRepository()


@notes_bp.route("/<string:note_id>", methods=["PATCH"])
def update_note(note_id, **kwargs):
    note = note_repository.get_by_id(note_id)
    if note is None:
        return jsonify({"error": "not_found", "message": "заметка не найдена"}), 404

    task = task_repository.get_by_id(note.task_id)
    if task is None:
        return jsonify({"error": "not_found", "message": "задача не найдена"}), 404

    user_id = current_user_id()
    if not permission_service.can_edit_task(task, user_id):
        return permission_denied_response("Недостаточно прав для редактирования задачи")

    payload = request.get_json(silent=True) or {}
    updated = note_repository.update(
        note_id, content_json=payload.get("contentJSON"), updated_by=user_id,
    )
    task_repository.touch_activity(note.task_id)
    return jsonify(domain_to_dto.note(updated).model_dump(by_alias=True))
