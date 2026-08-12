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

Роль manager (руководитель отдела/службы, ManagerDepartmentORM.user_id -> множество
участкованных department_id, т.к. один руководитель может вести несколько
отделов/служб одновременно): видит/редактирует все списки с list.department_id
в своих участках (даже без membership) и любые задачи, где список/исполнитель/
создатель относятся к такому отделу -- аналогично роли owner/editor, но по 'organisational'
признаку вместо list membership. Сам руководитель не может удалять список/управлять
участниками (CAN_MANAGE_MEMBERS/CAN_DELETE_LIST остаются только для owner/admin) -- это чисто
"расширенная видимость + редактирование задач", а не владелец списка.
Граница действует независимо от текущего global_role пользователя (смотрится только
наличие записей в ManagerDepartmentORM), чтобы админ мог назначать участки отделами и
администраторам, если потребуется -- глобальный admin в таком случае всё равно видит всё
через is_global_admin bypass.

Встречи (meetings) по-прежнему видны любому авторизованному пользователю (без ACL --
см. app.meetings.routes) -- meeting.department_id сейчас только справочная метка, в этот шаг не входит.

Видимость задач, привязанных к встрече (task.meeting_id): обычный пользователь,
добавленный участником встречи (MeetingAttendeeORM), должен видеть задачи этой встречи,
даже если он не состоит в membership списка задачи и не является исполнителем/создателем
(см. is_meeting_attendee / can_view_task_via_meeting -- инцидент "обычный пользователь
должен видеть только свои задачи и задачи в рамках встречи или списка, куда он добавлен
участником").

Формат ошибок для mutating-endpoints: JSON 403
    {"error": "permission_denied", "message": "..."}
чтобы frontend мог стабильно превращать такой ответ в PermissionDeniedError.
"""

from functools import wraps

from flask import jsonify

from app.auth.security import current_user_id
from app.domain import entities as d
from app.mappers import orm_to_domain
from app.models import (
    ListMembershipORM,
    ListORM,
    ManagerDepartmentORM,
    MeetingAttendeeORM,
    TaskORM,
    TaskTagORM,
    TaskWatcherORM,
    UserORM,
)

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

    def get_managed_department_ids(self, user_id: str):
        """Отделы/службы, которыми управляет данный пользователь (может быть
        несколько -- см. ManagerDepartmentORM). Не завязано на global_role,
        достаточно самих записей в manager_departments.
        """
        if not user_id:
            return []
        rows = ManagerDepartmentORM.query.filter_by(user_id=user_id).all()
        return [row.department_id for row in rows]

    def manages_department(self, user_id: str, department_id) -> bool:
        if not department_id:
            return False
        return department_id in self.get_managed_department_ids(user_id)

    def _list_department_id(self, list_id):
        if not list_id:
            return None
        row = ListORM.query.get(list_id)
        return row.department_id if row else None

    def _user_department_id(self, user_id):
        if not user_id:
            return None
        user = self._get_user(user_id)
        return user.department_id if user else None

    def is_meeting_attendee(self, meeting_id: str, user_id: str) -> bool:
        """Состоит ли user_id в участниках встречи meeting_id (MeetingAttendeeORM).
        Используется для видимости задач, привязанных к встрече (task.meeting_id),
        обычным пользователям без list membership -- см. can_view_task_via_meeting.
        """
        if not meeting_id or not user_id:
            return False
        return (
            MeetingAttendeeORM.query.filter_by(meeting_id=meeting_id, user_id=user_id).first()
            is not None
        )

    def can_view_task_via_meeting(self, task: d.Task, user_id: str) -> bool:
        """Видимость задачи по участию во встрече, к которой она привязана
        (task.meeting_id) -- независимо от list membership/organisational
        видимости руководителя. Любой участник встречи (MeetingAttendeeORM)
        видит все задачи этой встречи.
        """
        return self.is_meeting_attendee(task.meeting_id, user_id)

    def get_role(self, list_id: str, user_id: str):
        if not list_id or not user_id:
            return None
        membership = ListMembershipORM.query.filter_by(list_id=list_id, user_id=user_id).first()
        return membership.role if membership else None

    def can_view_list(self, list_id: str, user_id: str) -> bool:
        if self.is_global_admin(user_id):
            return True
        role = self.get_role(list_id, user_id)
        if role is not None:
            return True
        return self.manages_department(user_id, self._list_department_id(list_id))

    def can_create_task(self, list_id: str, user_id: str) -> bool:
        if self.is_global_admin(user_id):
            return True
        role = self.get_role(list_id, user_id)
        if role in CAN_EDIT_ANY_TASK:
            return True
        return self.manages_department(user_id, self._list_department_id(list_id))

    def can_edit_task(self, task: d.Task, user_id: str) -> bool:
        if self.is_global_admin(user_id):
            return True
        if not task.list_id:
            if task.created_by == user_id or task.assignee_id == user_id:
                return True
            return self.manages_department(user_id, self._user_department_id(task.assignee_id))
        role = self.get_role(task.list_id, user_id)
        if role in CAN_EDIT_ANY_TASK:
            return True
        if role == LIST_ROLE_ASSIGNEE and task.assignee_id == user_id:
            return True
        if self.manages_department(user_id, self._list_department_id(task.list_id)):
            return True
        return self.manages_department(user_id, self._user_department_id(task.assignee_id))

    def can_assign(self, list_id: str, user_id: str) -> bool:
        if self.is_global_admin(user_id):
            return True
        role = self.get_role(list_id, user_id)
        if role in CAN_EDIT_ANY_TASK:
            return True
        return self.manages_department(user_id, self._list_department_id(list_id))

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
            return self.manages_department(user_id, self._user_department_id(task.assignee_id))
        role = self.get_role(task.list_id, user_id)
        if role in CAN_EDIT_ANY_TASK:
            return True
        return self.manages_department(user_id, self._list_department_id(task.list_id))

    def get_accessible_list_ids(self, user_id: str):
        if self.is_global_admin(user_id):
            rows = ListMembershipORM.query.all()
            return sorted({row.list_id for row in rows})
        ids = {row.list_id for row in ListMembershipORM.query.filter_by(user_id=user_id).all()}
        managed_department_ids = self.get_managed_department_ids(user_id)
        if managed_department_ids:
            department_rows = ListORM.query.filter(ListORM.department_id.in_(managed_department_ids)).all()
            ids.update(row.id for row in department_rows)
        return list(ids)

    def is_task_visible(self, task: d.Task, role=None, user_id=None, is_global_admin=False) -> bool:
        if is_global_admin:
            return True
        if not role:
            return False
        if role == LIST_ROLE_ASSIGNEE:
            return task.assignee_id == user_id or user_id in (task.watcher_ids or [])
        return True

    def can_view_task_via_department(self, task: d.Task, user_id: str) -> bool:
        """Видимость задачи "по организационной принадлежности", независимо
        от list membership -- для руководителя отдела/службы (см. модуль-докстрайку).
        Задача видна, если её список/исполнитель/создатель относится к одному
        из отделов, которыми управляет user_id.
        """
        managed_department_ids = self.get_managed_department_ids(user_id)
        if not managed_department_ids:
            return False
        if task.list_id and self._list_department_id(task.list_id) in managed_department_ids:
            return True
        if self._user_department_id(task.assignee_id) in managed_department_ids:
            return True
        if self._user_department_id(task.created_by) in managed_department_ids:
            return True
        return False

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
