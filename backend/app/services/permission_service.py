"""
Зеркальное продолжение frontend `src/services/PermissionService.js` на backend.

Цель: backend становится источником истины для ACL, а frontend-проверки
(`PermissionService`, `useTaskPermissions`, `useListPermissions`) остаются
UX-слоем предварительной блокировки кнопок/действий.

Правила намеренно повторяют frontend почти дословно:
- глобальный `user.global_role == 'admin'` даёт полный bypass;
- Owner/Editor могут редактировать любые задачи списка;
- Assignee может редактировать только назначенную ему задачу;
- для задач без списка (`task.list_id is None`) действует упрощённая модель:
  редактировать может только создатель или текущий исполнитель;
- Assignee-участник списка видит только свои задачи или задачи, где он watcher.

Формат ошибок для mutating-endpoints: JSON 403
    {"error": "permission_denied", "message": "..."}
чтобы frontend мог стабильно превращать такой ответ в PermissionDeniedError.
"""

from functools import wraps

from flask import jsonify

from app.auth.security import current_user_id
from app.domain import entities as d
from app.mappers import orm_to_domain
from app.models import ListMembershipORM, TaskORM, TaskTagORM, TaskWatcherORM, UserORM

LIST_ROLE_OWNER = "owner"
LIST_ROLE_EDITOR = "editor"
LIST_ROLE_ASSIGNEE = "assignee"
LIST_ROLE_VIEWER = "viewer"

CAN_EDIT_ANY_TASK = {LIST_ROLE_OWNER, LIST_ROLE_EDITOR}
CAN_MANAGE_MEMBERS = {LIST_ROLE_OWNER}
CAN_DELETE_LIST = {LIST_ROLE_OWNER}


class PermissionService:
    """Backend-эквивалент frontend PermissionService."""

    def _get_user(self, user_id: str):
        if not user_id:
            return None
        return UserORM.query.get(user_id)

    def is_global_admin(self, user_id: str) -> bool:
        user = self._get_user(user_id)
        return bool(user and user.global_role == "admin")

    def get_role(self, list_id: str, user_id: str):
        if not list_id or not user_id:
            return None
        membership = ListMembershipORM.query.filter_by(list_id=list_id, user_id=user_id).first()
        return membership.role if membership else None

    def can_view_list(self, list_id: str, user_id: str) -> bool:
        if self.is_global_admin(user_id):
            return True
        role = self.get_role(list_id, user_id)
        return role is not None

    def can_create_task(self, list_id: str, user_id: str) -> bool:
        if self.is_global_admin(user_id):
            return True
        role = self.get_role(list_id, user_id)
        return role in CAN_EDIT_ANY_TASK

    def can_edit_task(self, task: d.Task, user_id: str) -> bool:
        if self.is_global_admin(user_id):
            return True
        if not task.list_id:
            return task.created_by == user_id or task.assignee_id == user_id
        role = self.get_role(task.list_id, user_id)
        if role in CAN_EDIT_ANY_TASK:
            return True
        if role == LIST_ROLE_ASSIGNEE and task.assignee_id == user_id:
            return True
        return False

    def can_assign(self, list_id: str, user_id: str) -> bool:
        if self.is_global_admin(user_id):
            return True
        role = self.get_role(list_id, user_id)
        return role in CAN_EDIT_ANY_TASK

    def can_manage_members(self, list_id: str, user_id: str) -> bool:
        if self.is_global_admin(user_id):
            return True
        role = self.get_role(list_id, user_id)
        return role in CAN_MANAGE_MEMBERS

    def can_delete_list(self, list_id: str, user_id: str) -> bool:
        if self.is_global_admin(user_id):
            return True
        role = self.get_role(list_id, user_id)
        return role in CAN_DELETE_LIST

    def can_delete_task(self, task: d.Task, user_id: str) -> bool:
        if self.is_global_admin(user_id):
            return True
        if task.created_by == user_id:
            return True
        if not task.list_id:
            return False
        role = self.get_role(task.list_id, user_id)
        return role in CAN_EDIT_ANY_TASK

    def get_accessible_list_ids(self, user_id: str):
        if self.is_global_admin(user_id):
            rows = ListMembershipORM.query.all()
            return sorted({row.list_id for row in rows})
        rows = ListMembershipORM.query.filter_by(user_id=user_id).all()
        return [row.list_id for row in rows]

    def is_task_visible(self, task: d.Task, role=None, user_id=None, is_global_admin=False) -> bool:
        if is_global_admin:
            return True
        if not role:
            return False
        if role == LIST_ROLE_ASSIGNEE:
            return task.assignee_id == user_id or user_id in (task.watcher_ids or [])
        return True

    def get_task_domain(self, task_id: str):
        row = TaskORM.query.get(task_id)
        if row is None:
            return None
        watcher_rows = TaskWatcherORM.query.filter_by(task_id=task_id).all()
        tag_rows = TaskTagORM.query.filter_by(task_id=task_id).all()
        watcher_ids = [watcher.user_id for watcher in watcher_rows]
        tags = [tag.tag for tag in tag_rows]
        return orm_to_domain.task(row, watcher_ids=watcher_ids, tags=tags)


permission_service = PermissionService()


def permission_denied_response(message: str):
    return jsonify({"error": "permission_denied", "message": message}), 403


def require_list_permission(permission_method_name: str, list_kwarg: str = "list_id"):
    """Guard для routes, которые оперируют конкретным списком.

    Пример:
        @require_list_permission("can_manage_members")
        def add_member(list_id): ...
    """

    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user_id = current_user_id()
            list_id = kwargs.get(list_kwarg)
            checker = getattr(permission_service, permission_method_name)
            if not checker(list_id, user_id):
                return permission_denied_response("Недостаточно прав для доступа к списку")
            return view(*args, **kwargs)

        return wrapper

    return decorator


def require_task_permission(permission_method_name: str, task_kwarg: str = "task_id"):
    """Guard для routes, которые оперируют конкретной задачей.

    Пример:
        @require_task_permission("can_edit_task")
        def update_task(task_id): ...
    """

    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user_id = current_user_id()
            task_id = kwargs.get(task_kwarg)
            task = permission_service.get_task_domain(task_id)
            if task is None:
                return jsonify({"error": "not_found", "message": "Задача не найдена"}), 404
            checker = getattr(permission_service, permission_method_name)
            if not checker(task, user_id):
                return permission_denied_response("Недостаточно прав для доступа к задаче")
            return view(*args, **kwargs)

        return wrapper

    return decorator
