"""
Реализация blueprint 'meetings' поверх MeetingRepository (app.repositories).

Доступконтроль: встречи видны любому авторизованному пользователю
(как и в mock-режиме -- нет ACL на уровне встреч в текущем domain-модели), также
как уже было в src/services -- см. backend/README.md.

unfinishedCount в MeetingResponseDTO -- агрегация "не выполнено в серии",
посчитана backend'ом (MeetingRepository.unfinished_total_count) -- см. комментарий
в MeetingRepository и backend/README.md.
"""

from flask import jsonify, request

from app.auth.security import current_user_id
from app.mappers import domain_to_dto
from app.meetings import meetings_bp
from app.repositories import MeetingRepository

meeting_repository = MeetingRepository()


def _not_found():
    return jsonify({"error": "not_found", "message": "встреча не найдена"}), 404


def _validation_error(details):
    return jsonify({"error": "validation_error", "details": details}), 400


@meetings_bp.route("", methods=["GET"])
def list_meetings(**kwargs):
    meetings = meeting_repository.get_all()
    return jsonify([domain_to_dto.meeting(m).model_dump(by_alias=True) for m in meetings])


@meetings_bp.route("", methods=["POST"])
def create_meeting(**kwargs):
    user_id = current_user_id()
    payload = request.get_json(silent=True) or {}
    title = payload.get("title")
    date = payload.get("date")
    if not title or not date:
        return _validation_error([{"loc": ["title/date"], "msg": "required"}])

    meeting = meeting_repository.create(
        title=title,
        date=date,
        description=payload.get("description", ""),
        link=payload.get("link", ""),
        color=payload.get("color", "#4f7cff"),
        recurrence=payload.get("recurrence"),
        attendee_ids=payload.get("attendeeIds", []),
        created_by=payload.get("createdBy", user_id),
        order=payload.get("order", 0),
    )
    return jsonify(domain_to_dto.meeting(meeting).model_dump(by_alias=True)), 201


@meetings_bp.route("/<string:meeting_id>", methods=["GET"])
def get_meeting(meeting_id, **kwargs):
    meeting = meeting_repository.get_by_id(meeting_id)
    if meeting is None:
        return _not_found()
    return jsonify(domain_to_dto.meeting(meeting).model_dump(by_alias=True))


@meetings_bp.route("/<string:meeting_id>", methods=["PATCH"])
def update_meeting(meeting_id, **kwargs):
    payload = request.get_json(silent=True) or {}
    field_map = {
        "title": "title", "date": "date", "description": "description", "link": "link",
        "color": "color", "archived": "archived", "order": "order", "recurrence": "recurrence",
        "attendeeIds": "attendee_ids", "occurrences": "occurrences",
    }
    patch = {snake: payload[camel] for camel, snake in field_map.items() if camel in payload}

    meeting = meeting_repository.update(meeting_id, patch)
    if meeting is None:
        return _not_found()
    return jsonify(domain_to_dto.meeting(meeting).model_dump(by_alias=True))


@meetings_bp.route("/<string:meeting_id>", methods=["DELETE"])
def delete_meeting(meeting_id, **kwargs):
    deleted = meeting_repository.delete(meeting_id)
    if not deleted:
        return _not_found()
    return "", 204


@meetings_bp.route("/<string:meeting_id>/occurrences", methods=["GET"])
def list_meeting_occurrences(meeting_id, **kwargs):
    meeting = meeting_repository.get_by_id(meeting_id)
    if meeting is None:
        return _not_found()
    occurrences = meeting_repository.list_occurrences(meeting_id)
    return jsonify([domain_to_dto.meeting_occurrence(o).model_dump(by_alias=True) for o in occurrences])
