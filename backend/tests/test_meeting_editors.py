"""
Права назначенного редактора встречи (meeting_editors):

- редактор может делать ВСЕ правки встречи (PATCH /api/meetings/:id), кроме
  удаления (DELETE возвращает 403);
- редактор может редактировать ВСЕ поля задач этой встречи, назначенных
  другим исполнителям (переименование, исполнитель, сроки, приоритет, статус);
- удаление задач встречи редактору недоступно (DELETE /api/tasks/:id -> 403);
- рядовой участник встречи без роли редактора правок встречи и чужих задач
  не имеет.
"""
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

from app.extensions import db
from app.models import MeetingAttendeeORM, MeetingEditorORM, MeetingORM
from tests.conftest import login, make_task, make_user


def _make_meeting(*, created_by, title="Planning"):
    now = datetime.now(timezone.utc)
    meeting = MeetingORM(
        id=str(uuid.uuid4()), title=title, date=now, description="", link="",
        color="#4f7cff", archived=False, order_index=0, recurrence=None,
        created_by=created_by, created_at=now,
    )
    db.session.add(meeting)
    db.session.commit()
    return meeting


def make_meeting_editor_world(app):
    """Пользователи/встреча/задача + SimpleNamespace-заглушки пользователей
    (id + login), чтобы не обращаться к ORM-объектам вне app_context."""
    with app.app_context():
        creator = make_user(login="mtg-creator")
        editor = make_user(login="mtg-editor")
        attendee = make_user(login="mtg-attendee")
        meeting = _make_meeting(created_by=creator.id)
        db.session.add(MeetingAttendeeORM(meeting_id=meeting.id, user_id=editor.id))
        db.session.add(MeetingAttendeeORM(meeting_id=meeting.id, user_id=attendee.id))
        db.session.add(MeetingEditorORM(meeting_id=meeting.id, user_id=editor.id))
        db.session.commit()
        # Задача встречи, созданная автором и назначенная на другого участника
        task = make_task(title="Attendee action", created_by=creator.id, assignee_id=attendee.id)
        task.meeting_id = meeting.id
        db.session.commit()
        return {
            "creator": SimpleNamespace(id=creator.id, login=creator.login),
            "editor": SimpleNamespace(id=editor.id, login=editor.login),
            "attendee": SimpleNamespace(id=attendee.id, login=attendee.login),
            "meeting_id": meeting.id,
            "task_id": task.id,
        }


def test_editor_can_edit_meeting_but_not_delete(client, app):
    world = make_meeting_editor_world(app)
    login(client, world["editor"])

    patched = client.patch(f"/api/meetings/{world['meeting_id']}", json={"title": "Renamed by editor"})
    assert patched.status_code == 200, patched.get_json()
    assert patched.get_json()["title"] == "Renamed by editor"

    assert client.delete(f"/api/meetings/{world['meeting_id']}").status_code == 403

    # Автор по-прежнему может удалить встречу
    login(client, world["creator"])
    assert client.delete(f"/api/meetings/{world['meeting_id']}").status_code == 204


def test_attendee_without_editor_role_cannot_edit_meeting(client, app):
    world = make_meeting_editor_world(app)
    login(client, world["attendee"])
    assert client.patch(
        f"/api/meetings/{world['meeting_id']}", json={"title": "Nope"}
    ).status_code == 403

    # Патч только порядка (drag-n-drop сортировка) остаётся доступен участнику
    assert client.patch(
        f"/api/meetings/{world['meeting_id']}", json={"order": 5}
    ).status_code == 200


def test_editor_can_toggle_status_of_other_assignees_tasks(client, app):
    world = make_meeting_editor_world(app)
    login(client, world["editor"])

    done = client.patch(
        f"/api/tasks/{world['task_id']}",
        json={"status": "done", "completedAt": "2026-09-10T10:00:00.000Z"},
    )
    assert done.status_code == 200, done.get_json()
    assert done.get_json()["status"] == "done"

    reopened = client.patch(f"/api/tasks/{world['task_id']}", json={"status": "open", "completedAt": None})
    assert reopened.status_code == 200
    assert reopened.get_json()["status"] == "open"


def test_editor_can_edit_all_fields_of_other_assignees_tasks(client, app):
    world = make_meeting_editor_world(app)
    login(client, world["editor"])

    # Переименование
    renamed = client.patch(f"/api/tasks/{world['task_id']}", json={"title": "Renamed by editor"})
    assert renamed.status_code == 200, renamed.get_json()
    assert renamed.get_json()["title"] == "Renamed by editor"

    # Смена срока и приоритета
    rescheduled = client.patch(
        f"/api/tasks/{world['task_id']}",
        json={"dueDate": "2026-09-20T09:00:00.000Z", "priority": "high"},
    )
    assert rescheduled.status_code == 200
    assert rescheduled.get_json()["priority"] == "high"

    # Смена исполнителя на участника встречи (сам редактор -- тоже участник)
    reassigned = client.patch(f"/api/tasks/{world['task_id']}", json={"assigneeId": world["editor"].id})
    assert reassigned.status_code == 200, reassigned.get_json()
    assert reassigned.get_json()["assigneeId"] == world["editor"].id

    # Назначение вне круга участников встречи по-прежнему блокируется валидацией
    with app.app_context():
        outsider = make_user(login="mtg-outsider")
        outsider_id = outsider.id
    rejected = client.patch(f"/api/tasks/{world['task_id']}", json={"assigneeId": outsider_id})
    assert rejected.status_code == 400


def test_editor_cannot_delete_meeting_tasks(client, app):
    world = make_meeting_editor_world(app)
    login(client, world["editor"])
    assert client.delete(f"/api/tasks/{world['task_id']}").status_code == 403

    # Автор задачи удалять может
    login(client, world["creator"])
    assert client.delete(f"/api/tasks/{world['task_id']}").status_code == 204


def test_attendee_without_rights_cannot_toggle_foreign_task(client, app):
    world = make_meeting_editor_world(app)
    login(client, world["attendee"])
    # Задача назначена на самого участника -- ему можно (обычное правило assignee)
    ok = client.patch(f"/api/tasks/{world['task_id']}", json={"status": "done"})
    assert ok.status_code == 200

    # А чужую задачу другой встречи участник без роли редактора отметить не может
    with app.app_context():
        creator = make_user(login="mtg-creator-2")
        other = make_user(login="mtg-other")
        meeting = _make_meeting(created_by=creator.id, title="Second")
        db.session.add(MeetingAttendeeORM(meeting_id=meeting.id, user_id=world["attendee"].id))
        db.session.add(MeetingAttendeeORM(meeting_id=meeting.id, user_id=other.id))
        db.session.commit()
        foreign = make_task(title="Foreign action", created_by=creator.id, assignee_id=other.id)
        foreign.meeting_id = meeting.id
        db.session.commit()
        foreign_id = foreign.id

    denied = client.patch(f"/api/tasks/{foreign_id}", json={"status": "done"})
    assert denied.status_code == 403
