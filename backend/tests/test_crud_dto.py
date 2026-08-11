"""
Промпт 20: CRUD-тесты для tasks/lists с проверкой camelCase DTO-контракта,
который ожидает frontend (src/repositories/http/*, apiClient.js).
"""

from tests.conftest import PASSWORD, make_user


def _login(client, login_name):
    resp = client.post("/api/auth/login", json={"login": login_name, "password": PASSWORD})
    assert resp.status_code == 200, resp.get_json()
    return resp


TASK_CAMEL_CASE_FIELDS = {
    "id", "listId", "parentTaskId", "title", "description", "status", "priority",
    "assigneeId", "watcherIds", "dueDate", "startDate", "recurrenceTemplateId",
    "tags", "pinned", "createdAt", "createdBy", "updatedAt", "updatedBy",
    "lastActivityAt", "completedAt", "displayStandalone", "meetingId", "occurrenceId",
}

LIST_CAMEL_CASE_FIELDS = {
    "id", "title", "description", "color", "ownerIds", "isShared", "defaultView",
    "settings", "archived", "order", "createdAt",
}


class TestTaskCrud:
    def test_create_task_returns_camel_case_dto(self, client, app):
        with app.app_context():
            make_user(login="task-crud-user")
        _login(client, "task-crud-user")

        resp = client.post("/api/tasks", json={"title": "Buy milk", "description": "2%"})

        assert resp.status_code == 201
        body = resp.get_json()
        assert set(body.keys()) == TASK_CAMEL_CASE_FIELDS
        assert body["title"] == "Buy milk"
        assert body["description"] == "2%"
        assert body["status"] == "open"
        assert body["priority"] == "medium"
        assert body["pinned"] is False
        assert body["watcherIds"] == []
        assert body["tags"] == []
        assert "created_at" not in body
        assert "list_id" not in body

    def test_get_task_returns_created_task(self, client, app):
        with app.app_context():
            make_user(login="task-crud-user2")
        _login(client, "task-crud-user2")

        create_resp = client.post("/api/tasks", json={"title": "Task A"})
        task_id = create_resp.get_json()["id"]

        get_resp = client.get(f"/api/tasks/{task_id}")
        assert get_resp.status_code == 200
        assert get_resp.get_json()["id"] == task_id
        assert get_resp.get_json()["title"] == "Task A"

    def test_patch_task_updates_fields(self, client, app):
        with app.app_context():
            make_user(login="task-crud-user3")
        _login(client, "task-crud-user3")

        task_id = client.post("/api/tasks", json={"title": "Old title"}).get_json()["id"]

        patch_resp = client.patch(
            f"/api/tasks/{task_id}",
            json={"title": "New title", "status": "done", "pinned": True},
        )

        assert patch_resp.status_code == 200
        body = patch_resp.get_json()
        assert body["title"] == "New title"
        assert body["status"] == "done"
        assert body["pinned"] is True
        assert "completedAt" in body

    def test_delete_task_removes_it(self, client, app):
        with app.app_context():
            make_user(login="task-crud-user4")
        _login(client, "task-crud-user4")

        task_id = client.post("/api/tasks", json={"title": "Delete me"}).get_json()["id"]

        delete_resp = client.delete(f"/api/tasks/{task_id}")
        assert delete_resp.status_code == 204

        get_resp = client.get(f"/api/tasks/{task_id}")
        assert get_resp.status_code == 404

    def test_list_tasks_returns_array_of_camel_case_dtos(self, client, app):
        with app.app_context():
            make_user(login="task-crud-user5")
        _login(client, "task-crud-user5")

        client.post("/api/tasks", json={"title": "T1"})
        client.post("/api/tasks", json={"title": "T2"})

        resp = client.get("/api/tasks")
        assert resp.status_code == 200
        body = resp.get_json()
        assert isinstance(body, list)
        assert len(body) >= 2
        for item in body:
            assert "dueDate" in item
            assert "due_date" not in item

    def test_create_task_requires_title(self, client, app):
        with app.app_context():
            make_user(login="task-crud-user6")
        _login(client, "task-crud-user6")

        resp = client.post("/api/tasks", json={})
        assert resp.status_code == 400
        assert resp.get_json()["error"] == "validation_error"


class TestListCrud:
    def test_create_list_returns_camel_case_dto(self, client, app):
        with app.app_context():
            make_user(login="list-crud-user")
        _login(client, "list-crud-user")

        resp = client.post("/api/lists", json={"title": "Groceries", "isShared": True})

        assert resp.status_code == 201
        body = resp.get_json()
        assert set(body.keys()) == LIST_CAMEL_CASE_FIELDS
        assert body["title"] == "Groceries"
        assert body["isShared"] is True
        assert isinstance(body["ownerIds"], list) and len(body["ownerIds"]) == 1
        assert "is_shared" not in body
        assert "owner_ids" not in body

    def test_creator_becomes_owner_and_can_view_own_list(self, client, app):
        with app.app_context():
            user = make_user(login="list-crud-user2")
            user_id = user.id
        _login(client, "list-crud-user2")

        create_resp = client.post("/api/lists", json={"title": "My list"})
        list_id = create_resp.get_json()["id"]
        assert create_resp.get_json()["ownerIds"] == [user_id]

        get_resp = client.get(f"/api/lists/{list_id}")
        assert get_resp.status_code == 200

    def test_patch_list_updates_fields(self, client, app):
        with app.app_context():
            make_user(login="list-crud-user3")
        _login(client, "list-crud-user3")

        list_id = client.post("/api/lists", json={"title": "Old"}).get_json()["id"]

        patch_resp = client.patch(f"/api/lists/{list_id}", json={"title": "New", "archived": True})

        assert patch_resp.status_code == 200
        body = patch_resp.get_json()
        assert body["title"] == "New"
        assert body["archived"] is True

    def test_delete_list_removes_it(self, client, app):
        with app.app_context():
            make_user(login="list-crud-user4")
        _login(client, "list-crud-user4")

        list_id = client.post("/api/lists", json={"title": "To delete"}).get_json()["id"]

        delete_resp = client.delete(f"/api/lists/{list_id}")
        assert delete_resp.status_code == 204

        get_resp = client.get(f"/api/lists/{list_id}")
        assert get_resp.status_code == 404

    def test_list_lists_only_returns_accessible_lists(self, client, app):
        with app.app_context():
            make_user(login="list-crud-user5")
            make_user(login="list-crud-user6")

        _login(client, "list-crud-user5")
        own_list_id = client.post("/api/lists", json={"title": "A's list"}).get_json()["id"]

        _login(client, "list-crud-user6")
        resp = client.get("/api/lists")
        ids = [item["id"] for item in resp.get_json()]
        assert own_list_id not in ids
