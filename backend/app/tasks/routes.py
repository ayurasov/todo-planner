"""Task API routes."""
import json
from flask import jsonify, request
from app.auth.security import current_user_id
from app.mappers import domain_to_dto
from app.models import ListORM
from app.repositories import ChecklistItemRepository, CommentRepository, NoteRepository, TaskRepository
from app.repositories.recurrence_repository import RecurrenceRepository
from app.services.history_service import history_service
from app.services.permission_service import permission_denied_response, permission_service, require_task_permission
from app.tasks import tasks_bp

task_repository = TaskRepository()
checklist_repository = ChecklistItemRepository()
note_repository = NoteRepository()
comment_repository = CommentRepository()
recurrence_repository = RecurrenceRepository()

def _not_found(name="задача"):
    return jsonify({"error":"not_found", "message":f"{name} не найдена"}), 404

def _validation_error(details): return jsonify({"error":"validation_error", "details":details}), 400
def _split_csv(value): return [v for v in value.split(",") if v] if value else None

def _task_json(task):
    body = domain_to_dto.task(task).model_dump(by_alias=True)
    body["meetingTitle"] = getattr(task, "meeting_title", None)
    body["occurrenceDate"] = getattr(task, "occurrence_date", None)
    return body

def _can_view_task(task, user_id):
    if permission_service.is_global_admin(user_id) or task.assignee_id == user_id:
        return True
    if permission_service.can_view_task_via_meeting(task, user_id): return True
    if task.list_id is None:
        return task.created_by == user_id or permission_service.can_view_task_via_department(task, user_id)
    role = permission_service.get_role(task.list_id, user_id)
    return permission_service.is_task_visible(task, role=role, user_id=user_id, is_global_admin=False) or permission_service.can_view_task_via_department(task, user_id)

def _list_allows_comments(list_id):
    if not list_id: return True
    row = ListORM.query.get(list_id)
    if row is None: return True
    settings = row.settings if isinstance(row.settings, dict) else {}
    return settings.get("allowComments", True) is not False

@tasks_bp.route("", methods=["GET"])
def list_tasks(**kwargs):
    tasks = task_repository.get_visible_for_user(current_user_id(), list_id=request.args.get("listId"), assignee_id=request.args.get("assigneeId"), statuses=_split_csv(request.args.get("status")), parent_task_id=request.args.get("parentTaskId"), tags=_split_csv(request.args.get("tags")))
    list_ids = _split_csv(request.args.get("listIds"))
    if list_ids: tasks = [t for t in tasks if t.list_id in list_ids]
    return jsonify([_task_json(t) for t in tasks])

@tasks_bp.route("", methods=["POST"])
def create_task(**kwargs):
    user_id = current_user_id(); payload = request.get_json(silent=True) or {}; title = payload.get("title")
    if not title: return _validation_error([{"loc":["title"],"msg":"required"}])
    list_id = payload.get("listId")
    if list_id and not permission_service.can_create_task(list_id, user_id): return permission_denied_response("Недостаточно прав для создания задачи в этом списке")
    task = task_repository.create(list_id=list_id, parent_task_id=payload.get("parentTaskId"), title=title, description=payload.get("description",""), status=payload.get("status","open"), priority=payload.get("priority","medium"), assignee_id=payload.get("assigneeId"), watcher_ids=payload.get("watcherIds",[]), due_date=payload.get("dueDate"), start_date=payload.get("startDate"), recurrence_template_id=payload.get("recurrenceTemplateId"), tags=payload.get("tags",[]), pinned=payload.get("pinned",False), created_by=user_id, meeting_id=payload.get("meetingId"), occurrence_id=payload.get("occurrenceId"))
    history_service.record_created(task.id, user_id)
    return jsonify(_task_json(task)), 201

@tasks_bp.route("/<string:task_id>", methods=["GET"])
def get_task(task_id, **kwargs):
    task = task_repository.get_by_id(task_id)
    if task is None: return _not_found()
    if not _can_view_task(task, current_user_id()): return permission_denied_response("Недостаточно прав для доступа к задаче")
    return jsonify(_task_json(task))

@tasks_bp.route("/<string:task_id>", methods=["PATCH"])
@require_task_permission("can_edit_task")
def update_task(task_id, **kwargs):
    user_id=current_user_id(); task=task_repository.get_by_id(task_id)
    if task is None: return _not_found()
    payload=request.get_json(silent=True) or {}
    field_map={"title":"title","description":"description","status":"status","priority":"priority","assigneeId":"assignee_id","watcherIds":"watcher_ids","dueDate":"due_date","startDate":"start_date","tags":"tags","pinned":"pinned","displayStandalone":"display_standalone","completedAt":"completed_at","meetingId":"meeting_id","occurrenceId":"occurrence_id"}
    patch={s:payload[c] for c,s in field_map.items() if c in payload}; old={s:getattr(task,s) for s in patch}
    updated=task_repository.touch_activity(task_id) if not patch else task_repository.update(task_id,patch,updated_by=user_id)
    if patch.get("status")=="done" and old.get("status")!="done":
        history_service.record_completed(task_id,user_id); recurrence_repository.on_task_completed(updated,task_repository=task_repository)
    return jsonify(_task_json(updated))

@tasks_bp.route("/<string:task_id>", methods=["DELETE"])
@require_task_permission("can_delete_task")
def delete_task(task_id, **kwargs):
    if not task_repository.delete(task_id): return _not_found()
    return "",204

@tasks_bp.route("/<string:task_id>/checklist-items", methods=["GET"])
def list_checklist(task_id, **kwargs):
    task=task_repository.get_by_id(task_id)
    if task is None: return _not_found()
    if not _can_view_task(task,current_user_id()): return permission_denied_response("Недостаточно прав для доступа к задаче")
    return jsonify([domain_to_dto.checklist_item(i).model_dump(by_alias=True) for i in checklist_repository.get_by_task_id(task_id)])

@tasks_bp.route("/<string:task_id>/notes", methods=["GET"])
def list_notes(task_id, **kwargs):
    task=task_repository.get_by_id(task_id)
    if task is None: return _not_found()
    if not _can_view_task(task,current_user_id()): return permission_denied_response("Недостаточно прав для доступа к задаче")
    return jsonify([domain_to_dto.note(n).model_dump(by_alias=True) for n in note_repository.get_by_task_id(task_id)])

@tasks_bp.route("/<string:task_id>/comments", methods=["GET"])
def list_comments(task_id, **kwargs):
    task=task_repository.get_by_id(task_id)
    if task is None: return _not_found()
    if not _can_view_task(task,current_user_id()): return permission_denied_response("Недостаточно прав для доступа к задаче")
    return jsonify([domain_to_dto.comment(c).model_dump(by_alias=True) for c in comment_repository.get_by_task_id(task_id)])

@tasks_bp.route("/<string:task_id>/history", methods=["GET"])
def get_history(task_id, **kwargs):
    task=task_repository.get_by_id(task_id)
    if task is None: return _not_found()
    if not _can_view_task(task,current_user_id()): return permission_denied_response("Недостаточно прав для доступа к задаче")
    return jsonify([domain_to_dto.history_entry(e).model_dump(by_alias=True) for e in history_service.get_task_timeline(task_id)])

@tasks_bp.route("/<string:task_id>/attachments", methods=["GET","POST"])
def attachments(**kwargs): return jsonify({"message":"task attachments not implemented"}),501
