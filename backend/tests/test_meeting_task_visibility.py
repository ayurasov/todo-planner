"""Backend task metadata regression tests.

These tests intentionally remain focused on the access boundary: an assignee can
read the task and its derived meeting labels, but cannot read the meeting itself.
"""
from datetime import datetime, timezone
from tests.conftest import login, make_user, make_task
from app.models import MeetingAttendeeORM, MeetingOccurrenceORM, MeetingORM
from app.extensions import db
import uuid


def test_assignee_sees_meeting_task_but_not_meeting(client, app):
    with app.app_context():
        creator = make_user(login="meeting-owner")
        assignee = make_user(login="meeting-assignee")
        meeting = MeetingORM(id=str(uuid.uuid4()), title="Hidden planning", date=datetime.now(timezone.utc), description="", link="", color="#4f7cff", archived=False, order_index=0, recurrence=None, created_by=creator.id, created_at=datetime.now(timezone.utc))
        db.session.add(meeting); db.session.commit()
        occurrence = MeetingOccurrenceORM(id=str(uuid.uuid4()), meeting_id=meeting.id, date=datetime.now(timezone.utc), description="", link="", generated_at=datetime.now(timezone.utc))
        db.session.add(occurrence); db.session.commit()
        task = make_task(title="Assigned action", created_by=creator.id, assignee_id=assignee.id)
        task.meeting_id = meeting.id; task.occurrence_id = occurrence.id; db.session.commit()

    login(client, assignee)
    tasks = client.get("/api/tasks"); assert tasks.status_code == 200
    body = next(item for item in tasks.get_json() if item["id"] == task.id)
    assert body["meetingTitle"] == "Hidden planning"
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
