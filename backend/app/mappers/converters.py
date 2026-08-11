"""
Явные функции преобразования между слоями backend v2:

    ORM (app.models)  --orm_to_domain-->  Domain (app.domain.entities)
    Domain             --domain_to_dto-->  DTO (app.dto)
    DTO (request)      --dto_to_domain-->  Domain

Здесь нет доступа к БД и нет бизнес-логики -- только чистое преобразование
данных. Это единственное место в проекте, которое "знает" обо всех трёх
слоях одновременно; routes/services (следующие шаги) должны дальше работать
только через domain-объекты и импортировать сюда лишь готовые функции.

Пример потока для задачи (см. README backend/README.md, раздел
"ORM / domain / DTO слои"):

    task_orm = TaskORM.query.get(task_id)          # persistence
    task = orm_to_domain.task(task_orm)             # -> Task (dataclass)
    dto = domain_to_dto.task(task)                  # -> TaskResponseDTO
    return jsonify(dto.model_dump(by_alias=True))   # camelCase JSON для фронта
"""

import json
from typing import Optional

from app.domain import entities as d
from app import dto as api_dto
from app import models as orm


def _loads(value, default):
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


class orm_to_domain:
    """ORM-модель (app.models) -> domain dataclass (app.domain.entities)."""

    @staticmethod
    def user(row: orm.UserORM) -> d.User:
        return d.User(
            id=row.id,
            name=row.name,
            email=row.email,
            timezone=row.timezone,
            avatar_url=row.avatar_url,
            global_role=row.global_role,
            is_active=bool(row.is_active),
            login=row.login,
            password_hash=row.password_hash,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def todo_list(row: orm.ListORM, owner_ids: Optional[list] = None) -> d.TodoList:
        return d.TodoList(
            id=row.id,
            title=row.title,
            description=row.description,
            color=row.color,
            is_shared=bool(row.is_shared),
            default_view=row.default_view,
            settings=_loads(row.settings, {}),
            archived=bool(row.archived),
            order=row.order_index,
            owner_ids=owner_ids or [],
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def list_membership(row: orm.ListMembershipORM) -> d.ListMembership:
        return d.ListMembership(
            id=row.id,
            list_id=row.list_id,
            user_id=row.user_id,
            role=row.role,
            added_at=row.added_at,
        )

    @staticmethod
    def task(row: orm.TaskORM, watcher_ids: Optional[list] = None, tags: Optional[list] = None) -> d.Task:
        return d.Task(
            id=row.id,
            list_id=row.list_id,
            parent_task_id=row.parent_task_id,
            title=row.title,
            description=row.description,
            status=row.status,
            priority=row.priority,
            assignee_id=row.assignee_id,
            watcher_ids=watcher_ids or [],
            due_date=row.due_date,
            start_date=row.start_date,
            recurrence_template_id=row.recurrence_template_id,
            tags=tags or [],
            pinned=bool(row.pinned),
            created_at=row.created_at,
            created_by=row.created_by,
            updated_at=row.updated_at,
            updated_by=row.updated_by,
            last_activity_at=row.last_activity_at,
            completed_at=row.completed_at,
            display_standalone=bool(row.display_standalone),
            meeting_id=row.meeting_id,
            occurrence_id=row.occurrence_id,
        )

    @staticmethod
    def meeting(row: orm.MeetingORM, attendee_ids: Optional[list] = None, occurrences: Optional[list] = None,
                unfinished_count: int = 0) -> d.Meeting:
        return d.Meeting(
            id=row.id,
            title=row.title,
            date=row.date,
            description=row.description,
            created_by=row.created_by,
            created_at=row.created_at,
            attendee_ids=attendee_ids or [],
            color=row.color,
            archived=bool(row.archived),
            order=row.order_index,
            link=row.link,
            recurrence=_loads(row.recurrence, None),
            occurrences=occurrences or [],
            unfinished_count=unfinished_count,
        )

    @staticmethod
    def meeting_occurrence(row: orm.MeetingOccurrenceORM) -> d.MeetingOccurrence:
        return d.MeetingOccurrence(
            id=row.id,
            meeting_id=row.meeting_id,
            date=row.date,
            description=row.description,
            link=row.link,
            generated_at=row.generated_at,
        )

    @staticmethod
    def recurrence_template(row: orm.RecurrenceTemplateORM) -> d.RecurrenceTemplate:
        return d.RecurrenceTemplate(
            id=row.id,
            list_id=row.list_id,
            title_template=row.title_template,
            type=row.type,
            rule=_loads(row.rule, {}),
            timezone=row.timezone,
            generate_ahead_count=row.generate_ahead_count,
            last_generated_instance_date=row.last_generated_instance_date,
            checklist_template=_loads(row.checklist_template, []),
        )

    @staticmethod
    def checklist_item(row: orm.ChecklistItemORM) -> d.ChecklistItem:
        return d.ChecklistItem(
            id=row.id,
            task_id=row.task_id,
            title=row.title,
            done=bool(row.done),
            order=row.order_index,
            recurrence_scope=row.recurrence_scope,
        )

    @staticmethod
    def note(row: orm.NoteORM) -> d.Note:
        return d.Note(
            id=row.id,
            task_id=row.task_id,
            content_json=_loads(row.content, {"type": "doc", "content": []}),
            created_at=row.created_at,
            updated_at=row.updated_at,
            updated_by=row.updated_by,
        )

    @staticmethod
    def attachment(row: orm.AttachmentORM) -> d.Attachment:
        return d.Attachment(
            id=row.id,
            file_name=row.file_name,
            mime_type=row.mime_type,
            url=row.url,
            size=row.size,
            task_id=row.task_id,
            note_id=row.note_id,
            uploaded_by=row.uploaded_by,
            uploaded_at=row.uploaded_at,
        )

    @staticmethod
    def history_entry(row: orm.TaskHistoryEntryORM) -> d.HistoryEntry:
        return d.HistoryEntry(
            id=row.id,
            task_id=row.task_id,
            actor_id=row.actor_id,
            type=row.type,
            timestamp=row.timestamp,
            field=row.field,
            old_value=row.old_value,
            new_value=row.new_value,
            comment=row.comment,
        )

    @staticmethod
    def comment(row: orm.CommentORM, mentions: Optional[list] = None) -> d.Comment:
        return d.Comment(
            id=row.id,
            task_id=row.task_id,
            author_id=row.author_id,
            text=row.text,
            created_at=row.created_at,
            edited_at=row.edited_at,
            mentions=mentions or [],
        )

    @staticmethod
    def saved_view(row: orm.SavedViewORM) -> d.SavedView:
        return d.SavedView(
            id=row.id,
            user_id=row.user_id,
            name=row.name,
            filters=_loads(row.filters, {}),
            sort=_loads(row.sort, {"field": "score", "dir": "desc"}),
            group_by=row.group_by,
            pinned=bool(row.pinned),
        )

    @staticmethod
    def notification(row: orm.NotificationORM) -> d.Notification:
        return d.Notification(
            id=row.id,
            user_id=row.user_id,
            type=row.type,
            title=row.title,
            body=row.body,
            task_id=row.task_id,
            list_id=row.list_id,
            actor_id=row.actor_id,
            created_at=row.created_at,
            read=bool(row.read),
        )

    @staticmethod
    def reminder_trigger(row: orm.ReminderTriggerORM) -> d.ReminderTrigger:
        return d.ReminderTrigger(
            id=row.id,
            task_id=row.task_id,
            type=row.type,
            time_offset=row.time_offset,
            geo=_loads(row.geo, None),
            is_enabled=bool(row.is_enabled),
        )

    @staticmethod
    def calendar_integration(row: orm.CalendarIntegrationORM) -> d.CalendarIntegration:
        return d.CalendarIntegration(
            id=row.id,
            user_id=row.user_id,
            provider=row.provider,
            status=row.status,
            sync_settings=_loads(row.sync_settings, {}),
            last_synced_at=row.last_synced_at,
        )


class domain_to_dto:
    """Domain dataclass (app.domain.entities) -> response DTO (app.dto)."""

    @staticmethod
    def user(u: d.User) -> api_dto.UserResponseDTO:
        return api_dto.UserResponseDTO(
            id=u.id, name=u.name, email=u.email, timezone=u.timezone,
            avatar_url=u.avatar_url, global_role=u.global_role, is_active=u.is_active,
        )

    @staticmethod
    def todo_list(l: d.TodoList) -> api_dto.ListResponseDTO:
        return api_dto.ListResponseDTO(
            id=l.id, title=l.title, description=l.description, color=l.color,
            owner_ids=l.owner_ids, is_shared=l.is_shared, default_view=l.default_view,
            created_at=l.created_at, settings=l.settings, archived=l.archived, order=l.order,
        )

    @staticmethod
    def list_membership(m: d.ListMembership) -> api_dto.ListMembershipResponseDTO:
        return api_dto.ListMembershipResponseDTO(
            id=m.id, list_id=m.list_id, user_id=m.user_id, role=m.role, added_at=m.added_at,
        )

    @staticmethod
    def task(t: d.Task) -> api_dto.TaskResponseDTO:
        return api_dto.TaskResponseDTO(
            id=t.id, list_id=t.list_id, parent_task_id=t.parent_task_id, title=t.title,
            description=t.description, status=t.status, priority=t.priority,
            assignee_id=t.assignee_id, watcher_ids=t.watcher_ids, due_date=t.due_date,
            start_date=t.start_date, recurrence_template_id=t.recurrence_template_id,
            tags=t.tags, pinned=t.pinned, created_at=t.created_at, created_by=t.created_by,
            updated_at=t.updated_at, updated_by=t.updated_by, last_activity_at=t.last_activity_at,
            completed_at=t.completed_at, display_standalone=t.display_standalone,
            meeting_id=t.meeting_id, occurrence_id=t.occurrence_id,
        )

    @staticmethod
    def meeting_occurrence(o: d.MeetingOccurrence) -> api_dto.MeetingOccurrenceResponseDTO:
        return api_dto.MeetingOccurrenceResponseDTO(
            id=o.id, meeting_id=o.meeting_id, date=o.date, description=o.description,
            link=o.link, generated_at=o.generated_at,
        )

    @staticmethod
    def meeting(m: d.Meeting) -> api_dto.MeetingResponseDTO:
        return api_dto.MeetingResponseDTO(
            id=m.id, title=m.title, date=m.date, description=m.description,
            created_by=m.created_by, created_at=m.created_at, attendee_ids=m.attendee_ids,
            color=m.color, archived=m.archived, order=m.order, link=m.link,
            recurrence=m.recurrence,
            occurrences=[domain_to_dto.meeting_occurrence(o) for o in m.occurrences],
            unfinished_count=m.unfinished_count,
        )

    @staticmethod
    def recurrence_template(r: d.RecurrenceTemplate) -> api_dto.RecurrenceTemplateResponseDTO:
        return api_dto.RecurrenceTemplateResponseDTO(
            id=r.id, list_id=r.list_id, title_template=r.title_template, type=r.type,
            rule=r.rule, timezone=r.timezone, generate_ahead_count=r.generate_ahead_count,
            last_generated_instance_date=r.last_generated_instance_date,
            checklist_template=r.checklist_template,
        )

    @staticmethod
    def checklist_item(c: d.ChecklistItem) -> api_dto.ChecklistItemResponseDTO:
        return api_dto.ChecklistItemResponseDTO(
            id=c.id, task_id=c.task_id, title=c.title, done=c.done, order=c.order,
            recurrence_scope=c.recurrence_scope,
        )

    @staticmethod
    def note(n: d.Note) -> api_dto.NoteResponseDTO:
        return api_dto.NoteResponseDTO(
            id=n.id, task_id=n.task_id, content_json=n.content_json,
            created_at=n.created_at, updated_at=n.updated_at, updated_by=n.updated_by,
        )

    @staticmethod
    def attachment(a: d.Attachment) -> api_dto.AttachmentResponseDTO:
        return api_dto.AttachmentResponseDTO(
            id=a.id, task_id=a.task_id, note_id=a.note_id, file_name=a.file_name,
            mime_type=a.mime_type, url=a.url, size=a.size, uploaded_by=a.uploaded_by,
            uploaded_at=a.uploaded_at,
        )

    @staticmethod
    def history_entry(h: d.HistoryEntry) -> api_dto.HistoryEntryResponseDTO:
        return api_dto.HistoryEntryResponseDTO(
            id=h.id, task_id=h.task_id, actor_id=h.actor_id, timestamp=h.timestamp,
            type=h.type, field=h.field, old_value=h.old_value, new_value=h.new_value,
            comment=h.comment,
        )

    @staticmethod
    def comment(c: d.Comment) -> api_dto.CommentResponseDTO:
        return api_dto.CommentResponseDTO(
            id=c.id, task_id=c.task_id, author_id=c.author_id, text=c.text,
            created_at=c.created_at, edited_at=c.edited_at, mentions=c.mentions,
        )

    @staticmethod
    def saved_view(s: d.SavedView) -> api_dto.SavedViewResponseDTO:
        return api_dto.SavedViewResponseDTO(
            id=s.id, user_id=s.user_id, name=s.name, filters=s.filters, sort=s.sort,
            group_by=s.group_by, pinned=s.pinned,
        )

    @staticmethod
    def notification(n: d.Notification) -> api_dto.NotificationResponseDTO:
        return api_dto.NotificationResponseDTO(
            id=n.id, user_id=n.user_id, type=n.type, title=n.title, body=n.body,
            task_id=n.task_id, list_id=n.list_id, actor_id=n.actor_id,
            created_at=n.created_at, read=n.read,
        )


class dto_to_domain:
    """Request DTO (app.dto) -> domain dataclass (app.domain.entities).

    Используется в services/repositories при создании/обновлении сущностей.
    `id`, `created_at`/`updated_at` и другие серверные поля здесь
    сознательно не заполняются -- их назначает services/repository слой
    (генерация id, временные метки), а не DTO-маппер.
    """

    @staticmethod
    def task_from_create(dto_obj: api_dto.TaskCreateDTO) -> d.Task:
        return d.Task(
            id=None,
            list_id=dto_obj.list_id,
            parent_task_id=dto_obj.parent_task_id,
            title=dto_obj.title,
            description=dto_obj.description,
            status=dto_obj.status,
            priority=dto_obj.priority,
            assignee_id=dto_obj.assignee_id,
            watcher_ids=dto_obj.watcher_ids,
            due_date=dto_obj.due_date,
            start_date=dto_obj.start_date,
            recurrence_template_id=dto_obj.recurrence_template_id,
            tags=dto_obj.tags,
            pinned=dto_obj.pinned,
            meeting_id=dto_obj.meeting_id,
            occurrence_id=dto_obj.occurrence_id,
        )

    @staticmethod
    def apply_task_update(task: d.Task, dto_obj: api_dto.TaskUpdateDTO) -> d.Task:
        """Возвращает Task с точечно апплицированными полями из PATCH-DTO
        (только те, что были явно переданы клиентом)."""
        data = dto_obj.model_dump(exclude_unset=True, by_alias=False)
        for key, value in data.items():
            setattr(task, key, value)
        return task

    @staticmethod
    def list_from_create(dto_obj: api_dto.ListCreateDTO) -> d.TodoList:
        return d.TodoList(
            id=None,
            title=dto_obj.title,
            description=dto_obj.description,
            color=dto_obj.color,
            is_shared=dto_obj.is_shared,
            default_view=dto_obj.default_view,
            settings=dto_obj.settings,
        )

    @staticmethod
    def meeting_from_create(dto_obj: api_dto.MeetingCreateDTO) -> d.Meeting:
        return d.Meeting(
            id=None,
            title=dto_obj.title,
            date=dto_obj.date,
            description=dto_obj.description,
            attendee_ids=dto_obj.attendee_ids,
            color=dto_obj.color,
            link=dto_obj.link,
            recurrence=dto_obj.recurrence,
        )

    @staticmethod
    def recurrence_template_from_create(dto_obj: api_dto.RecurrenceTemplateCreateDTO) -> d.RecurrenceTemplate:
        return d.RecurrenceTemplate(
            id=None,
            list_id=dto_obj.list_id,
            title_template=dto_obj.title_template,
            type=dto_obj.type,
            rule=dto_obj.rule,
            timezone=dto_obj.timezone,
            generate_ahead_count=dto_obj.generate_ahead_count,
            checklist_template=dto_obj.checklist_template,
        )

    @staticmethod
    def saved_view_from_create(dto_obj: api_dto.SavedViewCreateDTO) -> d.SavedView:
        return d.SavedView(
            id=None,
            user_id=None,
            name=dto_obj.name,
            filters=dto_obj.filters,
            sort=dto_obj.sort,
            group_by=dto_obj.group_by,
            pinned=dto_obj.pinned,
        )

    @staticmethod
    def notification_from_create(dto_obj: api_dto.NotificationCreateDTO) -> d.Notification:
        """Создание через POST /notifications -- временное решение: due_soon/overdue
        уведомления в http-режиме всё ещё создаются на фронте (см. backend/README.md,
        раздел про client/server split и Промпт 19 про background jobs)."""
        return d.Notification(
            id=None,
            user_id=dto_obj.user_id,
            type=dto_obj.type,
            title=dto_obj.title,
            body=dto_obj.body,
            task_id=dto_obj.task_id,
            list_id=dto_obj.list_id,
            actor_id=dto_obj.actor_id,
        )
