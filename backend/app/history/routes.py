"""
Реализация blueprint 'history' (/api/history). Сами записи всегда
создаются backend'ом в момент мутаций задачи (см. app.services.history_service
и app.tasks.routes) -- эти эндтойнты только читают.

?taskId= -- история конкретной задачи (видима тому, кто видит задачу);
?listId= -- история всех видимых задач списка;
?userId= -- история задач, где актор == userId, в рамках analytics-scope текущего
пользователя (см. permission_service.get_analytics_scope_user_ids). Раньше было
жёстко "только своя история или admin", что не пускало руководителя отдела
смотреть историю своих подчинённых на странице аналитики (AnalyticsView.vue).
"""

from flask import jsonify, request

from app.auth.security import current_user_id
from app.history import history_bp
from app.mappers import domain_to_dto
from app.models import TaskHistoryEntryORM
from app.repositories import TaskRepository
from app.services.history_service import history_service
from app.services.permission_service import permission_denied_response, permission_service

task_repository = TaskRepository()


def _can_view_task(task, user_id):
    if permission_service.is_global_admin(user_id):
        return True
    if task.list_id is None:
        return task.created_by == user_id or task.assignee_id == user_id
    role = permission_service.get_role(task.list_id, user_id)
    return permission_service.is_task_visible(task, role=role, user_id=user_id, is_global_admin=False)


@history_bp.route("", methods=["GET"])
def list_history_entries(**kwargs):
    user_id = current_user_id()
    task_id = request.args.get("taskId")
    list_id = request.args.get("listId")
    filter_user_id = request.args.get("userId")

    if task_id:
        task = task_repository.get_by_id(task_id)
        if task is None:
            return jsonify([])
        if not _can_view_task(task, user_id):
            return permission_denied_response("Недостаточно прав для доступа к задаче")
        entries = history_service.get_task_timeline(task_id)
        return jsonify([domain_to_dto.history_entry(e).model_dump(by_alias=True) for e in entries])

    if list_id:
        if not permission_service.can_view_list(list_id, user_id):
            return permission_denied_response("Недостаточно прав для доступа к списку")
        tasks = task_repository.get_visible_for_user(user_id, list_id=list_id)
        entries = []
        for task in tasks:
            entries.extend(history_service.get_task_timeline(task.id))
        entries.sort(key=lambda e: e.timestamp or "")
        return jsonify([domain_to_dto.history_entry(e).model_dump(by_alias=True) for e in entries])

    if filter_user_id:
        scope_ids = permission_service.get_analytics_scope_user_ids(user_id)
        if scope_ids is not None and filter_user_id not in scope_ids:
            return permission_denied_response("Недостаточно прав для доступа к истории этого пользователя")
        rows = TaskHistoryEntryORM.query.filter_by(actor_id=filter_user_id).order_by(TaskHistoryEntryORM.timestamp.asc()).all()
        from app.mappers import orm_to_domain
        entries = [orm_to_domain.history_entry(row) for row in rows]
        return jsonify([domain_to_dto.history_entry(e).model_dump(by_alias=True) for e in entries])

    if not permission_service.is_global_admin(user_id):
        return permission_denied_response("Укажите taskId, listId или userId")
    rows = TaskHistoryEntryORM.query.order_by(TaskHistoryEntryORM.timestamp.asc()).all()
    from app.mappers import orm_to_domain
    entries = [orm_to_domain.history_entry(row) for row in rows]
    return jsonify([domain_to_dto.history_entry(e).model_dump(by_alias=True) for e in entries])


@history_bp.route("/<string:entry_id>", methods=["GET"])
def get_history_entry(entry_id, **kwargs):
    row = TaskHistoryEntryORM.query.get(entry_id)
    if row is None:
        return jsonify({"error": "not_found", "message": "запись истории не найдена"}), 404

    task = task_repository.get_by_id(row.task_id)
    user_id = current_user_id()
    if task is not None and not _can_view_task(task, user_id):
        return permission_denied_response("Недостаточно прав для доступа к задаче")

    from app.mappers import orm_to_domain
    entry = orm_to_domain.history_entry(row)
    return jsonify(domain_to_dto.history_entry(entry).model_dump(by_alias=True))
