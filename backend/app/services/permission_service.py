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

Назначенный редактор встречи (meeting_editors): может делать все правки
встречи, кроме удаления самой встречи (входит в can_edit_meeting, но НЕ в
can_delete_meeting), и имеет полные права на задачи своей встречи
(can_edit_task + can_delete_task), включая задачи других исполнителей:
переименование, исполнитель, сроки, приоритет, удаление и т.д.

Обычный пользователь по встречам видит только:
- свои встречи (created_by == user_id),
- встречи, где он явно добавлен участником (MeetingAttendeeORM),
- задачи этих встреч (task.meeting_id), даже если не состоит в membership списка.
Руководитель дополнительно видит все встречи отделов, которыми руководит
(meeting.department_id in managed_department_ids).

Область видимости аналитики (get_analytics_scope_user_ids, см. GET /api/analytics/scope
и GET /api/history?userId=): раньше страница аналитики (AnalyticsView.vue) молча
показывала статистику по всем сотрудникам компании любому авторизованному пользователю
(единственное ограничение было на чтение "чужой" истории по userId -- не связанное
с видимостью списка сотрудников/задач на самой странице). Это давало обычному
пользователю и руководителю отдела возможность видеть аналитику по людям, задачи и
списки которых им не видны в остальном приложении. get_analytics_scope_user_ids
возвращает None для глобального admin (без ограничений) и множество user_id для всех
остальных: сам пользователь + все сотрудники отделов, которыми он управляет (иначе --
только сам пользователь, аналогично видимости "своих" задач).

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
    MeetingEditorORM,
    MeetingORM,
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

    def _meeting_department_id(self, meeting_id):
        if not meeting_id:
            return None
        row = MeetingORM.query.get(meeting_id)
        return row.department_id if row else None

    def _user_department_id(self, user_id):
        if not user_id:
            return None
        user = self._get_user(user_id)
        return user.department_id if user else None

    def is_meeting_attendee(self, meeting_id: str, user_id: str) -> bool:
        if not meeting_id or not user_id:
            return False
        return (
            MeetingAttendeeORM.query.filter_by(meeting_id=meeting_id, user_id=user_id).first()
            is not None
        )

    def is_meeting_editor(self, meeting_id: str, user_id: str) -> bool:
        """Назначенный редактор встречи (meeting_editors): может делать все
        правки встречи, кроме удаления, и отмечать выполнение задач этой
        встречи (в том числе назначенных другим исполнителям)."""
        if not meeting_id or not user_id:
            return False
        return (
            MeetingEditorORM.query.filter_by(meeting_id=meeting_id, user_id=user_id).first()
            is not None
        )

    def can_view_task_via_meeting(self, task: d.Task, user_id: str) -> bool:
        return self.is_meeting_attendee(task.meeting_id, user_id)

    def can_view_meeting_via_department(self, meeting: d.Meeting, user_id: str) -> bool:
        return self.manages_department(user_id, self._meeting_department_id(meeting.id))

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

    def can_toggle_task_status(self, task: d.Task, user_id: str) -> bool:
        """Право на галочку выполнения (PATCH только status/completedAt).
        После расширения прав редактора встречи на все поля задач его встречи
        совпадает с can_edit_task; метод сохранён для зеркальности с frontend
        PermissionService.canToggleTaskStatus."""
        if self.is_global_admin(user_id):
            return True
        if self.can_edit_task(task, user_id):
            return True
        return self.is_meeting_editor(task.meeting_id, user_id)

    def can_edit_task(self, task: d.Task, user_id: str) -> bool:
        if self.is_global_admin(user_id):
            return True
        # Назначенный редактор встречи может редактировать ВСЕ поля задач
        # своей встречи (task.meeting_id), включая задачи других исполнителей.
        # Удаление задач при этом остаётся недоступным -- can_delete_task.
        if task.meeting_id and self.is_meeting_editor(task.meeting_id, user_id):
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
        # Назначенный редактор встречи может удалять задачи своей встречи
        # (саму встречу при этом удалить не может -- can_delete_meeting).
        if task.meeting_id and self.is_meeting_editor(task.meeting_id, user_id):
            return True
        if not task.list_id:
            return self.manages_department(user_id, self._user_department_id(task.assignee_id))
        role = self.get_role(task.list_id, user_id)
        if role in CAN_EDIT_ANY_TASK:
            return True
        return self.manages_department(user_id, self._list_department_id(task.list_id))

    def get_accessible_list_ids(self, user_id: str):
        if self.is_global_admin(user_id):
            rows = ListORM.query.all()
            return sorted(row.id for row in rows)
        ids = {row.list_id for row in ListMembershipORM.query.filter_by(user_id=user_id).all()}
        managed_department_ids = self.get_managed_department_ids(user_id)
        if managed_department_ids:
            department_rows = ListORM.query.filter(ListORM.department_id.in_(managed_department_ids)).all()
            ids.update(row.id for row in department_rows)
        return list(ids)

    def is_task_visible(self, task: d.Task, role=None, user_id=None, is_global_admin=False) -> bool:
        if is_global_admin:
            return True
        if task.created_by == user_id:
            return True
        if not role:
            return False
        if role == LIST_ROLE_ASSIGNEE:
            return task.assignee_id == user_id or user_id in (task.watcher_ids or [])
        return True

    def _meeting_related_list_ids(self, meeting_id):
        """Списки задач, связанных со встречей (task.meeting_id)."""
        if not meeting_id:
            return set()
        rows = TaskORM.query.filter_by(meeting_id=meeting_id).all()
        return {row.list_id for row in rows if row.list_id}

    def _is_related_list_manager(self, meeting: d.Meeting, user_id: str) -> bool:
        """Owner/Editor какого-либо списка, в котором есть задачи этой встречи.
        Зеркалит frontend-правило canManageMeeting в MeetingDetailView."""
        for list_id in self._meeting_related_list_ids(meeting.id):
            if self.get_role(list_id, user_id) in CAN_EDIT_ANY_TASK:
                return True
        return False

    def can_edit_meeting(self, meeting: d.Meeting, user_id: str) -> bool:
        """Все правки встречи: глобальный admin, автор встречи, назначенный
        редактор (meeting_editors) или owner/editor связанного списка задач."""
        if self.is_global_admin(user_id):
            return True
        if meeting.created_by == user_id:
            return True
        if self.is_meeting_editor(meeting.id, user_id):
            return True
        return self._is_related_list_manager(meeting, user_id)

    def can_delete_meeting(self, meeting: d.Meeting, user_id: str) -> bool:
        """Удаление встречи: назначенному редактору запрещено (в отличие от
        can_edit_meeting), удалять могут только admin, автор и owner/editor
        связанного списка задач."""
        if self.is_global_admin(user_id):
            return True
        if meeting.created_by == user_id:
            return True
        return self._is_related_list_manager(meeting, user_id)

    def can_view_task_via_department(self, task: d.Task, user_id: str) -> bool:
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

    def get_analytics_scope_user_ids(self, user_id: str):
        if self.is_global_admin(user_id):
            return None

        scope = {user_id} if user_id else set()
        managed_department_ids = self.get_managed_department_ids(user_id)
        if managed_department_ids:
            rows = UserORM.query.filter(UserORM.department_id.in_(managed_department_ids)).all()
            scope.update(row.id for row in rows)
        return scope

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
