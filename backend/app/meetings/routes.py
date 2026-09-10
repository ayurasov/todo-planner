"""
Реализация blueprint 'meetings' поверх MeetingRepository (app.repositories).

Доступконтроль:
- GET /meetings и GET /meetings/:id показывают только те встречи, которые доступны
  текущему пользователю: свои, встречи где он attendee, либо все встречи отделов,
  которыми он руководит.
- PATCH /meetings/:id -- все правки встречи: доступны автору, глобальному admin,
  назначенному редактору встречи (meeting_editors) и owner/editor связанного
  списка задач. Единственное исключение -- патч только с полем order
  (drag-n-drop сортировка на странице встреч): он разрешён любому, кто видит
  встречу, так как порядок -- UI-настройка, а не контент встречи.
- DELETE /meetings/:id -- только автор, глобальный admin или owner/editor
  связанного списка задач. Назначенный редактор встречи удалять её НЕ может.

unfinishedCount в MeetingResponseDTO -- агрегация "не выполнено в серии",
посчитана backend'ом (MeetingRepository.unfinished_total_count) -- см. комментарий
в MeetingRepository и backend/README.md.
"""

from flask import jsonify, request

from app.auth.security import current_user_id
from app.mappers import domain_to_dto
from app.meetings import meetings_bp
from app.repositories import MeetingRepository
from app.services.permission_service import permission_denied_response, permission_service

meeting_repository = MeetingRepository()


def _not_found():
    return jsonify({"error": "not_found", "message": "встреча не найдена"}), 404


def _validation_error(details):
    return jsonify({"error": "validation_error", "details": details}), 400


def _can_view_meeting(meeting, user_id):
    if permission_service.is_global_admin(user_id):
        return True
    if meeting.created_by == user_id:
        return True
    if user_id in (meeting.attendee_ids or []):
        return True
    return permission_service.can_view_meeting_via_department(meeting, user_id)


def _can_edit_meeting(meeting, user_id):
    return permission_service.can_edit_meeting(meeting, user_id)


def _can_delete_meeting(meeting, user_id):
    return permission_service.can_delete_meeting(meeting, user_id)


@meetings_bp.route("", methods=["GET"])
def list_meetings(**kwargs):
    user_id = current_user_id()
    meetings = [m for m in meeting_repository.get_all() if _can_view_meeting(m, user_id)]
    return jsonify([domain_to_dto.meeting(m).model_dump(by_alias=True) for m in meetings])


@meetings_bp.route("", methods=["POST"])
def create_meeting(**kwargs):
    user_id = current_user_id()
    payload = request.get_json(silent=True) or {}
    title = payload.get("title")
    date = payload.get("date")
    if not title or not date:
        return _validation_error([{"loc": ["title/date"], "msg": "required"}])

    # Автор автоматически попадает в участники встречи, чтобы случайно
    # себя не забыть (не участник -> не видит встречи/не может быть исполнителем).
    creator_id = payload.get("createdBy", user_id)
    attendee_ids = list(payload.get("attendeeIds", []) or [])
    if creator_id and creator_id not in attendee_ids:
        attendee_ids.append(creator_id)

    meeting = meeting_repository.create(
        title=title,
        date=date,
        description=payload.get("description", ""),
        link=payload.get("link", ""),
        color=payload.get("color", "#4f7cff"),
        recurrence=payload.get("recurrence"),
        attendee_ids=attendee_ids,
        editor_ids=payload.get("editorIds", []),
        created_by=creator_id,
        order=payload.get("order", 0),
    )
    return jsonify(domain_to_dto.meeting(meeting).model_dump(by_alias=True)), 201


@meetings_bp.route("/<string:meeting_id>", methods=["GET"])
def get_meeting(meeting_id, **kwargs):
    meeting = meeting_repository.get_by_id(meeting_id)
    if meeting is None:
        return _not_found()
    if not _can_view_meeting(meeting, current_user_id()):
        return permission_denied_response("Недостаточно прав для доступа к встрече")
    return jsonify(domain_to_dto.meeting(meeting).model_dump(by_alias=True))


@meetings_bp.route("/<string:meeting_id>", methods=["PATCH"])
def update_meeting(meeting_id, **kwargs):
    meeting = meeting_repository.get_by_id(meeting_id)
    if meeting is None:
        return _not_found()
    user_id = current_user_id()
    payload = request.get_json(silent=True) or {}
    field_map = {
        "title": "title", "date": "date", "description": "description", "link": "link",
        "color": "color", "archived": "archived", "order": "order", "recurrence": "recurrence",
        "attendeeIds": "attendee_ids", "editorIds": "editor_ids", "occurrences": "occurrences",
    }
    patch = {snake: payload[camel] for camel, snake in field_map.items() if camel in payload}
    # Патч только порядка (drag-n-drop сортировка) не считается правкой контента
    # встречи -- он разрешён любому, кто видит встречу (см. docstring модуля).
    reorder_only = set(patch) <= {"order"}
    if reorder_only:
        if not _can_view_meeting(meeting, user_id):
            return permission_denied_response("Недостаточно прав для доступа к встрече")
    elif not _can_edit_meeting(meeting, user_id):
        return permission_denied_response("Недостаточно прав для редактирования встречи")

    updated = meeting_repository.update(meeting_id, patch)
    if updated is None:
        return _not_found()
    return jsonify(domain_to_dto.meeting(updated).model_dump(by_alias=True))


@meetings_bp.route("/<string:meeting_id>", methods=["DELETE"])
def delete_meeting(meeting_id, **kwargs):
    meeting = meeting_repository.get_by_id(meeting_id)
    if meeting is None:
        return _not_found()
    if not _can_delete_meeting(meeting, current_user_id()):
        return permission_denied_response("Недостаточно прав для удаления встречи")
    deleted = meeting_repository.delete(meeting_id)
    if not deleted:
        return _not_found()
    return "", 204


@meetings_bp.route("/<string:meeting_id>/occurrences", methods=["GET"])
def list_meeting_occurrences(meeting_id, **kwargs):
    meeting = meeting_repository.get_by_id(meeting_id)
    if meeting is None:
        return _not_found()
    if not _can_view_meeting(meeting, current_user_id()):
        return permission_denied_response("Недостаточно прав для доступа к встрече")
    occurrences = meeting_repository.list_occurrences(meeting_id)
    return jsonify([domain_to_dto.meeting_occurrence(o).model_dump(by_alias=True) for o in occurrences])
