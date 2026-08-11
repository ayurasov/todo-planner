"""
Реализация blueprint 'recurrence' поверх RecurrenceRepository (app.repositories).

Генерация следующего инстанса задачи (RecurrenceService.js.onTaskCompleted)
выполняется не тут, а в app.tasks.routes.update_task при завершении задачи
(status -> done) -- см. backend/README.md.
"""

from flask import jsonify, request

from app.mappers import domain_to_dto
from app.recurrence import recurrence_bp
from app.repositories import RecurrenceRepository

recurrence_repository = RecurrenceRepository()


def _not_found():
    return jsonify({"error": "not_found", "message": "шаблон повторения не найден"}), 404


def _validation_error(details):
    return jsonify({"error": "validation_error", "details": details}), 400


@recurrence_bp.route("", methods=["GET"])
def list_recurrence_templates(**kwargs):
    templates = recurrence_repository.get_all(list_id=request.args.get("listId"))
    return jsonify([domain_to_dto.recurrence_template(t).model_dump(by_alias=True) for t in templates])


@recurrence_bp.route("", methods=["POST"])
def create_recurrence_template(**kwargs):
    payload = request.get_json(silent=True) or {}
    list_id = payload.get("listId")
    title_template = payload.get("titleTemplate")
    type_ = payload.get("type")
    if not list_id or not title_template or not type_:
        return _validation_error([{"loc": ["listId/titleTemplate/type"], "msg": "required"}])

    template = recurrence_repository.create(
        list_id=list_id,
        title_template=title_template,
        type=type_,
        rule=payload.get("rule", {}),
        timezone=payload.get("timezone", "Europe/Moscow"),
        generate_ahead_count=payload.get("generateAheadCount", 1),
        checklist_template=payload.get("checklistTemplate", []),
    )
    return jsonify(domain_to_dto.recurrence_template(template).model_dump(by_alias=True)), 201


@recurrence_bp.route("/<string:template_id>", methods=["GET"])
def get_recurrence_template(template_id, **kwargs):
    template = recurrence_repository.get_by_id(template_id)
    if template is None:
        return _not_found()
    return jsonify(domain_to_dto.recurrence_template(template).model_dump(by_alias=True))


@recurrence_bp.route("/<string:template_id>", methods=["PATCH"])
def update_recurrence_template(template_id, **kwargs):
    payload = request.get_json(silent=True) or {}
    field_map = {
        "titleTemplate": "title_template", "rule": "rule", "timezone": "timezone",
        "generateAheadCount": "generate_ahead_count", "checklistTemplate": "checklist_template",
        "lastGeneratedInstanceDate": "last_generated_instance_date",
    }
    patch = {snake: payload[camel] for camel, snake in field_map.items() if camel in payload}

    template = recurrence_repository.update(template_id, patch)
    if template is None:
        return _not_found()
    return jsonify(domain_to_dto.recurrence_template(template).model_dump(by_alias=True))


@recurrence_bp.route("/<string:template_id>", methods=["DELETE"])
def delete_recurrence_template(template_id, **kwargs):
    deleted = recurrence_repository.delete(template_id)
    if not deleted:
        return _not_found()
    return "", 204
