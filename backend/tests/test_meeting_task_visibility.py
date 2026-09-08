"""Backend task metadata regression tests.

These tests intentionally remain focused on the access boundary: an assignee can
read the task and its derived occurrence label, but cannot read the meeting itself.
"""
from datetime import datetime, timezone
from tests.conftest import login, make_user, make_task
from app.models import MeetingOccurrenceORM, MeetingORM
from app.extensions import db
import uuid


def test_assignee_sees_meeting_task_but_not_meeting(client, app):
    occurrence_date = datetime(2026, 9, 2, 12, 30, tzinfo=timezone.utc)
    with app.app_context():
        creator = make_user(login="meeting-owner")
        assignee = make_user(login="meeting-assignee")
        meeting = MeetingORM(id=str(uuid.uuid4()), title="Hidden planning", date=occurrence_date, description="", link="", color="#4f7cff", archived=False, order_index=0, recurrence=None, created_by=creator.id, created_at=occurrence_date)
        db.session.add(meeting); db.session.commit()
        occurrence = MeetingOccurrenceORM(id=str(uuid.uuid4()), meeting_id=meeting.id, date=occurrence_date, description="", link="", generated_at=occurrence_date)
        db.session.add(occurrence); db.session.commit()
        task = make_task(title="Assigned action", created_by=creator.id, assignee_id=assignee.id)
        task.meeting_id = meeting.id; task.occurrence_id = occurrence.id; db.session.commit()

    login(client, assignee)
    tasks = client.get("/api/tasks"); assert tasks.status_code == 200
    body = next(item for item in tasks.get_json() if item["id"] == task.id)
    assert body.get("meetingTitle") in (None, "")
    assert body["occurrenceTitle"] == "Подвстреча · 02.09.2026 12:30"
    assert body["occurrenceDate"]
    assert client.get(f"/api/tasks/{task.id}").status_code == 200
    assert client.get(f"/api/meetings/{meeting.id}").status_code in (403, 404)


def test_unrelated_user_does_not_see_meeting_task(client, app):
    with app.app_context():
        creator = make_user(login="meeting-owner-2")
        assignee = make_user(login="meeting-assignee-2")
        outsider = make_user(login="meeting-outsider-2")
        meeting = MeetingORM(id=str(uuid.uuid4()), title="Private meeting", date=datetime.now(timezone.utc), description="", link="", color="#4f7cff", archived=False, order_index=0, recurrence=None, created_by=creator.id, created_at=datetime.now(timezone.utc))
        db.session.add(meeting); db.session.commit()
        task = make_task(title="Private action", created_by=creator.id, assignee_id=assignee.id)
        task.meeting_id = meeting.id; db.session.commit()
    login(client, outsider)
    assert all(item["id"] != task.id for item in client.get("/api/tasks").get_json())
    assert client.get(f"/api/tasks/{task.id}").status_code in (403, 404)


def test_subtask_inherits_meeting_and_occurrence_and_rejects_non_attendee(client, app):
    occurrence_date = datetime(2026, 9, 3, 10, 0, tzinfo=timezone.utc)
    with app.app_context():
        owner = make_user(login="subtask-owner")
        attendee = make_user(login="subtask-attendee")
        outsider = make_user(login="subtask-outsider")
        meeting = MeetingORM(id=str(uuid.uuid4()), title="Recurring planning", date=occurrence_date, description="", link="", color="#4f7cff", archived=False, order_index=0, recurrence={"freq": "weekly"}, created_by=owner.id, created_at=occurrence_date)
        db.session.add(meeting)
        db.session.commit()
        from app.models import MeetingAttendeeORM
        db.session.add(MeetingAttendeeORM(meeting_id=meeting.id, user_id=attendee.id))
        db.session.commit()
        occurrence = MeetingOccurrenceORM(id=str(uuid.uuid4()), meeting_id=meeting.id, date=occurrence_date, description="", link="", generated_at=occurrence_date)
        db.session.add(occurrence)
        db.session.commit()
        parent = make_task(title="Parent", created_by=owner.id, assignee_id=attendee.id)
        parent.meeting_id = meeting.id
        parent.occurrence_id = occurrence.id
        db.session.commit()

    login(client, owner)
    response = client.post("/api/tasks", json={"parentTaskId": parent.id, "title": "Allowed subtask", "assigneeId": attendee.id})
    assert response.status_code == 201, response.get_json()
    child = response.get_json()
    assert child["meetingId"] == meeting.id
    assert child["occurrenceId"] == occurrence.id

    rejected = client.post("/api/tasks", json={"parentTaskId": parent.id, "title": "Rejected subtask", "assigneeId": outsider.id})
    assert rejected.status_code == 400


def test_comment_edit_and_delete_permissions(client, app):
    with app.app_context():
        task_owner = make_user(login="comment-task-owner")
        comment_author = make_user(login="comment-author")
        other = make_user(login="comment-other")
        admin = make_user(login="comment-admin", global_role="admin")
        task = make_task(title="Comment task", created_by=task_owner.id, assignee_id=task_owner.id)

    login(client, task_owner)
    created = client.post(f"/api/tasks/{task.id}/comments", json={"text": "<strong>Old</strong>"})
    assert created.status_code == 201
    comment_id = created.get_json()["id"]
    edited = client.patch(f"/api/tasks/comments/{comment_id}", json={"text": "<em>New</em>"})
    assert edited.status_code == 200
    assert edited.get_json()["text"] == "<em>New</em>"

    login(client, other)
    assert client.delete(f"/api/tasks/comments/{comment_id}").status_code == 403
    login(client, admin)
    assert client.delete(f"/api/tasks/comments/{comment_id}").status_code == 204
