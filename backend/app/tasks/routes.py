"""
Реализация blueprint 'tasks' поверх TaskRepository/ChecklistItemRepository/
NoteRepository/CommentRepository (app.repositories) и HistoryService (app.services).

Достуиконтроль:
  - GET /tasks -- видимые текущему пользователю задачи (server-side через
    TaskRepository.get_visible_for_user, а не "всё и фильтр на фронте").
  - POST /tasks -- если есть listId, требует can_create_task; без listId --
    "приватная" задача, доступна любому авторизованному.
  - GET /tasks/:id -- достуен любому, кто видит задачу (_can_view_task, включая
    is_task_visible, permission_service.can_view_task_via_department для роли manager и
    permission_service.can_view_task_via_meeting для участников встречи, к которой привязана задача),
    PATCH/DELETE -- @require_task_permission("can_edit_task"/"can_delete_task").
  - Сабресурсы (checklist-items/notes/comments) защищены правами
    родительской задачи: чтение -- через _can_view_task (та же видимость,
    что и для самой задачи), запись/удаление checklist/notes -- can_edit_task,
    комментарии доступны любому, кто видит задачу, если
    list.settings.allowComments != false (правило из tasksStore.addComment).
  - GET /tasks/:id/history -- через HistoryService.get_task_timeline (виден любому,
    кто видит задачу).

Рекуррентные задачи: когда update_task переводит задачу в status=done и у неё
есть recurrence_template_id, вызывается RecurrenceRepository.on_task_completed --
порт `src/services/RecurrenceService.js.onTaskCompleted` на backend, выполняется здесь,
а не только на фронте -- см. backend/README.md, раздел "Client/server split".
"""

import json

from flask import jsonify, request

from app.auth.security import current_user_id
from app.mappers import domain_to_dto
from app.models import ListORM
from app.repositories import ChecklistItemRepository, CommentRepository, NoteRepository, TaskRepository
from app.repositories.recurrence_repository import RecurrenceRepository
from app.services.history_service import history_service
from app.services.permission_service import (
    permission_denied_response,
    permission_service,
    require_task_permission,
)
from app.tasks import tasks_bp

task_repository = TaskRepository()
checklist_repository = ChecklistItemRepository()
note_repository = NoteRepository()
comment_repository = CommentRepository()
recurrence_repository = RecurrenceRepository()


def _not_found(name="задача"):
    return jsonify({"error": "not_found", "message": f"{name} не найдена"}), 404


def _validation_error(details):
    return jsonify({"error": "validation_error", "details": details}), 400


def _split_csv(value):
    return [v for v in value.split(",") if v] if value else None


def _can_view_task(task, user_id):
    if permission_service.is_global_admin(user_id):
        return True
    # участник встречи, к которой привязана задача, видит её независимо от
    # membership в списке -- см. permission_service.can_view_task_via_meeting.
    if permission_service.can_view_task_via_meeting(task, user_id):
        return True
    if task.list_id is None:
        if task.created_by == user_id or task.assignee_id == user_id:
            return True
        return permission_service.can_view_task_via_department(task, user_id)
    role = permission_service.get_role(task.list_id, user_id)
    if permission_service.is_task_visible(task, role=role, user_id=user_id, is_global_admin=False):
        return True
    # руководитель отдела/службы видит задачу даже без membership в списке,
    # если список/исполнитель/создатель относятся к его managed_department_ids.
    return permission_service.can_view_task_via_department(task, user_id)


def _list_allows_comments(list_id):
    if not list_id:
        return True
    row = ListORM.query.get(list_id)
    if row is None:
        return True
    try:
        settings = json.loads(row.settings) if row.settings else {}
    except (TypeError, ValueError):
        settings = {}
    return settings.get("allowComments", True) is not False


# --- Tasks ---

@tasks_bp.route("", methods=["GET"])
def list_tasks(**kwargs):
    user_id = current_user_id()
    tasks = task_repository.get_visible_for_user(
        user_id,
        list_id=request.args.get("listId"),
        assignee_id=request.args.get("assigneeId"),
        statuses=_split_csv(request.args.get("status")),
        parent_task_id=request.args.get("parentTaskId"),
        tags=_split_csv(request.args.get("tags")),
    )
    list_ids = _split_csv(request.args.get("listIds"))
    if list_ids:
        tasks = [t for t in tasks if t.list_id in list_ids]
    return jsonify([domain_to_dto.task(t).model_dump(by_alias=True) for t in tasks])


@tasks_bp.route("", methods=["POST"])
def create_task(**kwargs):
    user_id = current_user_id()
    payload = request.get_json(silent=True) or {}
    title = payload.get("title")
    if not title:
        return _validation_error([{"loc": ["title"], "msg": "required"}])

    list_id = payload.get("listId")
    if list_id and not permission_service.can_create_task(list_id, user_id):
        return permission_denied_response("Недостаточно прав для создания задачи в этом списке")

    task = task_repository.create(
        list_id=list_id,
        parent_task_id=payload.get("parentTaskId"),
        title=title,
        description=payload.get("description", ""),
        status=payload.get("status", "open"),
        priority=payload.get("priority", "medium"),
        assignee_id=payload.get("assigneeId"),
        watcher_ids=payload.get("watcherIds", []),
        due_date=payload.get("dueDate"),
        start_date=payload.get("startDate"),
        recurrence_template_id=payload.get("recurrenceTemplateId"),
        tags=payload.get("tags", []),
        pinned=payload.get("pinned", False),
        created_by=user_id,
        meeting_id=payload.get("meetingId"),
        occurrence_id=payload.get("occurrenceId"),
    )
    history_service.record_created(task.id, user_id)
    if task.parent_task_id:
        task_repository.touch_activity(task.parent_task_id)
    return jsonify(domain_to_dto.task(task).model_dump(by_alias=True)), 201


@tasks_bp.route("/<string:task_id>", methods=["GET"])
def get_task(task_id, **kwargs):
    task = task_repository.get_by_id(task_id)
    if task is None:
        return _not_found()
    if not _can_view_task(task, current_user_id()):
        return permission_denied_response("Недостаточно прав для доступа к задаче")
    return jsonify(domain_to_dto.task(task).model_dump(by_alias=True))


@tasks_bp.route("/<string:task_id>", methods=["PATCH"])
@require_task_permission("can_edit_task")
def update_task(task_id, **kwargs):
    user_id = current_user_id()
    task = task_repository.get_by_id(task_id)
    if task is None:
        return _not_found()

    payload = request.get_json(silent=True) or {}
    field_map = {
        "title": "title", "description": "description", "status": "status",
        "priority": "priority", "assigneeId": "assignee_id", "watcherIds": "watcher_ids",
        "dueDate": "due_date", "startDate": "start_date", "tags": "tags",
        "pinned": "pinned", "displayStandalone": "display_standalone", "completedAt": "completed_at",
        # meetingId/occurrenceId -- позволяет перепривязать задачу к другой подвстрече
        # серии (или снять привязку через null) прямо из карточки задачи, без
        # необходимости пересоздавать задачу внутри нужной подвстречи.
        "meetingId": "meeting_id", "occurrenceId": "occurrence_id",
    }
    patch = {}
    old_values = {}
    for camel_key, snake_key in field_map.items():
        if camel_key in payload:
            patch[snake_key] = payload[camel_key]
            old_values[snake_key] = getattr(task, snake_key)

    if not patch:
        # аналог tasksStore.touchActivity: PATCH без полей -- только обновить last_activity_at.
        updated = task_repository.touch_activity(task_id)
        return jsonify(domain_to_dto.task(updated).model_dump(by_alias=True))

    updated = task_repository.update(task_id, patch, updated_by=user_id)

    was_completed = old_values.get("status") == "done"
    is_completed_now = patch.get("status") == "done"
    is_reopened_now = patch.get("status") == "open" and old_values.get("status") == "done"

    if is_completed_now and not was_completed:
        history_service.record_completed(task_id, user_id)
        # Порт RecurrenceService.js.onTaskCompleted -- генерация следующего инстанса
        # для completion_based-шаблона выполняется на backend всегда (а не только на фронте),
        # чтобы работать одинаково для всех клиентов.
        recurrence_repository.on_task_completed(updated, task_repository=task_repository)
    elif is_reopened_now:
        history_service.record_reopened(task_id, user_id)

    for snake_key, old_value in old_values.items():
        if snake_key in ("status", "completed_at"):
            continue
        new_value = patch[snake_key]
        if snake_key == "assignee_id":
            history_service.record_assignee_changed(task_id, user_id, old_value, new_value)
        elif snake_key == "due_date":
            history_service.record_rescheduled(task_id, user_id, old_value, new_value)
        else:
            history_service.record_field_changed(task_id, user_id, snake_key, old_value, new_value)

    return jsonify(domain_to_dto.task(updated).model_dump(by_alias=True))


@tasks_bp.route("/<string:task_id>", methods=["DELETE"])
@require_task_permission("can_delete_task")
def delete_task(task_id, **kwargs):
    deleted = task_repository.delete(task_id)
    if not deleted:
        return _not_found()
    return "", 204


# --- Checklist items (вложенный ресурс задачи) ---

@tasks_bp.route("/<string:task_id>/checklist-items", methods=["GET"])
def list_task_checklist_items(task_id, **kwargs):
    task = task_repository.get_by_id(task_id)
    if task is None:
        return _not_found()
    if not _can_view_task(task, current_user_id()):
        return permission_denied_response("Недостаточно прав для доступа к задаче")
    items = checklist_repository.get_by_task_id(task_id)
    return jsonify([domain_to_dto.checklist_item(i).model_dump(by_alias=True) for i in items])


@tasks_bp.route("/<string:task_id>/checklist-items", methods=["POST"])
def create_task_checklist_item(task_id, **kwargs):
    user_id = current_user_id()
    task = task_repository.get_by_id(task_id)
    if task is None:
        return _not_found()
    if not permission_service.can_edit_task(task, user_id):
        return permission_denied_response("Недостаточно прав для редактирования задачи")

    payload = request.get_json(silent=True) or {}
    title = payload.get("title")
    if not title:
        return _validation_error([{"loc": ["title"], "msg": "required"}])

    item = checklist_repository.create(
        task_id=task_id, title=title, done=payload.get("done", False),
        order=payload.get("order", 0), recurrence_scope=payload.get("recurrenceScope", "instance_only"),
    )
    task_repository.touch_activity(task_id)
    return jsonify(domain_to_dto.checklist_item(item).model_dump(by_alias=True)), 201


# --- Notes (вложенный ресурс задачи) ---

@tasks_bp.route("/<string:task_id>/notes", methods=["GET"])
def get_task_note(task_id, **kwargs):
    task = task_repository.get_by_id(task_id)
    if task is None:
        return _not_found()
    if not _can_view_task(task, current_user_id()):
        return permission_denied_response("Недостаточно прав для доступа к задаче")
    notes = note_repository.get_by_task_id(task_id)
    return jsonify([domain_to_dto.note(n).model_dump(by_alias=True) for n in notes])


@tasks_bp.route("/<string:task_id>/notes", methods=["POST"])
def create_task_note(task_id, **kwargs):
    user_id = current_user_id()
    task = task_repository.get_by_id(task_id)
    if task is None:
        return _not_found()
    if not permission_service.can_edit_task(task, user_id):
        return permission_denied_response("Недостаточно прав для редактирования задачи")

    payload = request.get_json(silent=True) or {}
    note = note_repository.create(
        task_id=task_id, content_json=payload.get("contentJSON"), updated_by=user_id,
    )
    task_repository.touch_activity(task_id)
    return jsonify(domain_to_dto.note(note).model_dump(by_alias=True)), 201


# --- Comments (вложенный ресурс задачи) ---

@tasks_bp.route("/<string:task_id>/comments", methods=["GET"])
def list_task_comments(task_id, **kwargs):
    task = task_repository.get_by_id(task_id)
    if task is None:
        return _not_found()
    if not _can_view_task(task, current_user_id()):
        return permission_denied_response("Недостаточно прав для доступа к задаче")
    comments = comment_repository.get_by_task_id(task_id)
    return jsonify([domain_to_dto.comment(c).model_dump(by_alias=True) for c in comments])


@tasks_bp.route("/<string:task_id>/comments", methods=["POST"])
def create_task_comment(task_id, **kwargs):
    user_id = current_user_id()
    task = task_repository.get_by_id(task_id)
    if task is None:
        return _not_found()
    if not _can_view_task(task, user_id):
        return permission_denied_response("Недостаточно прав для доступа к задаче")

    if not _list_allows_comments(task.list_id):
        return permission_denied_response("Комментарии отключены владельцем списка")

    payload = request.get_json(silent=True) or {}
    text = payload.get("text")
    if not text:
        return _validation_error([{"loc": ["text"], "msg": "required"}])

    comment = comment_repository.create(
        task_id=task_id, author_id=user_id, text=text, mentions=payload.get("mentions", []),
    )
    history_service.record_comment(task_id, user_id, text)
    task_repository.touch_activity(task_id)
    return jsonify(domain_to_dto.comment(comment).model_dump(by_alias=True)), 201


# --- Attachments (остаётся 501 -- вне скопа этого шага) ---

@tasks_bp.route("/<string:task_id>/attachments", methods=["GET"])
def list_task_attachments(**kwargs):
    return jsonify({"message": "list_task_attachments not implemented"}), 501


@tasks_bp.route("/<string:task_id>/attachments", methods=["POST"])
def upload_task_attachment(**kwargs):
    return jsonify({"message": "upload_task_attachment not implemented"}), 501


# --- History (вложенный ресурс задачи) ---

@tasks_bp.route("/<string:task_id>/history", methods=["GET"])
def get_task_history(task_id, **kwargs):
    task = task_repository.get_by_id(task_id)
    if task is None:
        return _not_found()
    if not _can_view_task(task, current_user_id()):
        return permission_denied_response("Недостаточно прав для доступа к задаче")
    entries = history_service.get_task_timeline(task_id)
    return jsonify([domain_to_dto.history_entry(e).model_dump(by_alias=True) for e in entries])
