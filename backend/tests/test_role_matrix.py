"""
Integration-тесты (Промпт 18) на матрицу ролей: global admin, list owner,
list editor, list viewer, list assignee, пользователь без доступа к списку --
для view list / create task / edit task (свою/чужую) / delete task /
manage members / delete list.

Ожидаемые статусы 200/201/204/403/404 соответствуют таблице mapping в
backend/README.md ("PermissionService mirror").
"""

from tests.conftest import PASSWORD, add_membership, login, make_task


def _login_as(client, world, role_key):
    return login(client, world[role_key])


class TestViewList:
    def test_admin_can_view_any_list(self, client, role_matrix_world):
        _login_as(client, role_matrix_world, "admin")
        resp = client.get(f"/api/lists/{role_matrix_world['list'].id}")
        assert resp.status_code == 200

    def test_owner_editor_viewer_assignee_can_view_list(self, client, role_matrix_world):
        for role_key in ("owner", "editor", "viewer", "assignee"):
            _login_as(client, role_matrix_world, role_key)
            resp = client.get(f"/api/lists/{role_matrix_world['list'].id}")
            assert resp.status_code == 200, (role_key, resp.get_json())

    def test_outsider_cannot_view_list(self, client, role_matrix_world):
        _login_as(client, role_matrix_world, "outsider")
        resp = client.get(f"/api/lists/{role_matrix_world['list'].id}")
        assert resp.status_code == 403

    def test_get_lists_filters_server_side(self, client, role_matrix_world):
        """GET /lists не должен возвращать список, к которому у пользователя
        нет membership -- фильтрация происходит на backend (permission_service.
        get_accessible_list_ids), а не полагается на скрытие в UI.
        """
        _login_as(client, role_matrix_world, "outsider")
        resp = client.get("/api/lists")
        assert resp.status_code == 200
        ids = [item["id"] for item in resp.get_json()]
        assert role_matrix_world["list"].id not in ids

    def test_get_lists_includes_membership_for_viewer(self, client, role_matrix_world):
        _login_as(client, role_matrix_world, "viewer")
        resp = client.get("/api/lists")
        ids = [item["id"] for item in resp.get_json()]
        assert role_matrix_world["list"].id in ids

    def test_get_lists_admin_sees_all_including_no_membership(self, client, role_matrix_world):
        _login_as(client, role_matrix_world, "admin")
        resp = client.get("/api/lists")
        ids = [item["id"] for item in resp.get_json()]
        assert role_matrix_world["list"].id in ids


class TestCreateTask:
    def _create_task_payload(self, world):
        return {"title": "New task", "listId": world["list"].id}

    def test_admin_can_create_task(self, client, role_matrix_world):
        _login_as(client, role_matrix_world, "admin")
        resp = client.post("/api/tasks", json=self._create_task_payload(role_matrix_world))
        assert resp.status_code == 201

    def test_owner_and_editor_can_create_task(self, client, role_matrix_world):
        for role_key in ("owner", "editor"):
            _login_as(client, role_matrix_world, role_key)
            resp = client.post("/api/tasks", json=self._create_task_payload(role_matrix_world))
            assert resp.status_code == 201, (role_key, resp.get_json())

    def test_viewer_and_assignee_cannot_create_task(self, client, role_matrix_world):
        for role_key in ("viewer", "assignee"):
            _login_as(client, role_matrix_world, role_key)
            resp = client.post("/api/tasks", json=self._create_task_payload(role_matrix_world))
            assert resp.status_code == 403, (role_key, resp.get_json())

    def test_outsider_cannot_create_task(self, client, role_matrix_world):
        _login_as(client, role_matrix_world, "outsider")
        resp = client.post("/api/tasks", json=self._create_task_payload(role_matrix_world))
        assert resp.status_code == 403


class TestEditTask:
    def test_admin_can_edit_any_task(self, client, role_matrix_world):
        _login_as(client, role_matrix_world, "admin")
        resp = client.patch(f"/api/tasks/{role_matrix_world['task'].id}", json={"title": "Edited by admin"})
        assert resp.status_code == 200

    def test_owner_and_editor_can_edit_any_task_in_list(self, client, role_matrix_world):
        for role_key in ("owner", "editor"):
            _login_as(client, role_matrix_world, role_key)
            resp = client.patch(f"/api/tasks/{role_matrix_world['task'].id}", json={"title": f"Edited by {role_key}"})
            assert resp.status_code == 200, (role_key, resp.get_json())

    def test_assignee_can_edit_own_task(self, client, role_matrix_world, app):
        """Задача в фикстуре назначена на editor -- проверяем assignee на
        отдельной задаче, назначенной именно на него (своя задача)."""
        with app.app_context():
            own_task = make_task(
                list_id=role_matrix_world["list"].id,
                title="Assignee's own task",
                created_by=role_matrix_world["owner"].id,
                assignee_id=role_matrix_world["assignee"].id,
            )
            own_task_id = own_task.id
        _login_as(client, role_matrix_world, "assignee")
        resp = client.patch(f"/api/tasks/{own_task_id}", json={"title": "Edited by assignee"})
        assert resp.status_code == 200

    def test_assignee_cannot_edit_others_task(self, client, role_matrix_world):
        """Задача фикстуры назначена на editor, не на assignee -- assignee
        не должен иметь права её редактировать."""
        _login_as(client, role_matrix_world, "assignee")
        resp = client.patch(f"/api/tasks/{role_matrix_world['task'].id}", json={"title": "Should fail"})
        assert resp.status_code == 403

    def test_viewer_cannot_edit_task(self, client, role_matrix_world):
        _login_as(client, role_matrix_world, "viewer")
        resp = client.patch(f"/api/tasks/{role_matrix_world['task'].id}", json={"title": "Should fail"})
        assert resp.status_code == 403

    def test_outsider_cannot_edit_task(self, client, role_matrix_world):
        _login_as(client, role_matrix_world, "outsider")
        resp = client.patch(f"/api/tasks/{role_matrix_world['task'].id}", json={"title": "Should fail"})
        assert resp.status_code == 403

    def test_editing_nonexistent_task_returns_404(self, client, role_matrix_world):
        _login_as(client, role_matrix_world, "admin")
        resp = client.patch("/api/tasks/does-not-exist", json={"title": "x"})
        assert resp.status_code == 404


class TestDeleteTask:
    def test_admin_can_delete_any_task(self, client, role_matrix_world, app):
        with app.app_context():
            task_id = make_task(list_id=role_matrix_world["list"].id, created_by=role_matrix_world["owner"].id).id
        _login_as(client, role_matrix_world, "admin")
        resp = client.delete(f"/api/tasks/{task_id}")
        assert resp.status_code == 204

    def test_owner_and_editor_can_delete_task(self, client, role_matrix_world, app):
        for role_key in ("owner", "editor"):
            with app.app_context():
                task_id = make_task(list_id=role_matrix_world["list"].id, created_by=role_matrix_world["owner"].id).id
            _login_as(client, role_matrix_world, role_key)
            resp = client.delete(f"/api/tasks/{task_id}")
            assert resp.status_code == 204, (role_key, resp.get_json())

    def test_creator_can_delete_own_task_even_as_viewer(self, client, role_matrix_world, app):
        """canDeleteTask: создатель может удалить всегда, независимо от роли
        в списке (см. PermissionService.js/permission_service.py)."""
        with app.app_context():
            task_id = make_task(list_id=role_matrix_world["list"].id, created_by=role_matrix_world["viewer"].id).id
        _login_as(client, role_matrix_world, "viewer")
        resp = client.delete(f"/api/tasks/{task_id}")
        assert resp.status_code == 204

    def test_viewer_cannot_delete_others_task(self, client, role_matrix_world, app):
        with app.app_context():
            task_id = make_task(list_id=role_matrix_world["list"].id, created_by=role_matrix_world["owner"].id).id
        _login_as(client, role_matrix_world, "viewer")
        resp = client.delete(f"/api/tasks/{task_id}")
        assert resp.status_code == 403

    def test_assignee_cannot_delete_others_task(self, client, role_matrix_world, app):
        with app.app_context():
            task_id = make_task(list_id=role_matrix_world["list"].id, created_by=role_matrix_world["owner"].id).id
        _login_as(client, role_matrix_world, "assignee")
        resp = client.delete(f"/api/tasks/{task_id}")
        assert resp.status_code == 403

    def test_outsider_cannot_delete_task(self, client, role_matrix_world, app):
        with app.app_context():
            task_id = make_task(list_id=role_matrix_world["list"].id, created_by=role_matrix_world["owner"].id).id
        _login_as(client, role_matrix_world, "outsider")
        resp = client.delete(f"/api/tasks/{task_id}")
        assert resp.status_code == 403


class TestManageMembers:
    def _membership_payload(self, world):
        return {"userId": world["outsider"].id, "role": "viewer"}

    def test_admin_can_manage_members(self, client, role_matrix_world):
        _login_as(client, role_matrix_world, "admin")
        resp = client.post(f"/api/lists/{role_matrix_world['list'].id}/memberships", json=self._membership_payload(role_matrix_world))
        assert resp.status_code == 201

    def test_owner_can_manage_members(self, client, role_matrix_world):
        _login_as(client, role_matrix_world, "owner")
        resp = client.post(f"/api/lists/{role_matrix_world['list'].id}/memberships", json=self._membership_payload(role_matrix_world))
        assert resp.status_code == 201

    def test_editor_cannot_manage_members(self, client, role_matrix_world):
        _login_as(client, role_matrix_world, "editor")
        resp = client.post(f"/api/lists/{role_matrix_world['list'].id}/memberships", json=self._membership_payload(role_matrix_world))
        assert resp.status_code == 403

    def test_viewer_cannot_manage_members(self, client, role_matrix_world):
        _login_as(client, role_matrix_world, "viewer")
        resp = client.post(f"/api/lists/{role_matrix_world['list'].id}/memberships", json=self._membership_payload(role_matrix_world))
        assert resp.status_code == 403

    def test_outsider_cannot_manage_members(self, client, role_matrix_world):
        _login_as(client, role_matrix_world, "outsider")
        resp = client.post(f"/api/lists/{role_matrix_world['list'].id}/memberships", json=self._membership_payload(role_matrix_world))
        assert resp.status_code == 403

    def test_owner_can_remove_member(self, client, role_matrix_world):
        _login_as(client, role_matrix_world, "owner")
        resp = client.delete(f"/api/lists/{role_matrix_world['list'].id}/memberships/{role_matrix_world['viewer'].id}")
        assert resp.status_code == 204

    def test_editor_cannot_remove_member(self, client, role_matrix_world):
        _login_as(client, role_matrix_world, "editor")
        resp = client.delete(f"/api/lists/{role_matrix_world['list'].id}/memberships/{role_matrix_world['viewer'].id}")
        assert resp.status_code == 403


class TestDeleteList:
    def test_admin_can_delete_list(self, client, role_matrix_world):
        _login_as(client, role_matrix_world, "admin")
        resp = client.delete(f"/api/lists/{role_matrix_world['list'].id}")
        assert resp.status_code == 204

    def test_owner_can_delete_list(self, client, role_matrix_world):
        _login_as(client, role_matrix_world, "owner")
        resp = client.delete(f"/api/lists/{role_matrix_world['list'].id}")
        assert resp.status_code == 204

    def test_editor_cannot_delete_list(self, client, role_matrix_world):
        _login_as(client, role_matrix_world, "editor")
        resp = client.delete(f"/api/lists/{role_matrix_world['list'].id}")
        assert resp.status_code == 403

    def test_viewer_cannot_delete_list(self, client, role_matrix_world):
        _login_as(client, role_matrix_world, "viewer")
        resp = client.delete(f"/api/lists/{role_matrix_world['list'].id}")
        assert resp.status_code == 403

    def test_assignee_cannot_delete_list(self, client, role_matrix_world):
        _login_as(client, role_matrix_world, "assignee")
        resp = client.delete(f"/api/lists/{role_matrix_world['list'].id}")
        assert resp.status_code == 403

    def test_outsider_cannot_delete_list(self, client, role_matrix_world):
        _login_as(client, role_matrix_world, "outsider")
        resp = client.delete(f"/api/lists/{role_matrix_world['list'].id}")
        assert resp.status_code == 403

    def test_deleting_nonexistent_list_returns_404_for_admin(self, client, role_matrix_world):
        _login_as(client, role_matrix_world, "admin")
        resp = client.delete("/api/lists/does-not-exist")
        assert resp.status_code == 404


class TestUpdateList:
    """PATCH /lists/:id использует то же правило, что и canCreateTask
    (owner/editor) -- ср. backend/README.md, раздел PermissionService mirror."""

    def test_owner_and_editor_can_update_list(self, client, role_matrix_world):
        for role_key in ("owner", "editor"):
            _login_as(client, role_matrix_world, role_key)
            resp = client.patch(f"/api/lists/{role_matrix_world['list'].id}", json={"title": f"Renamed by {role_key}"})
            assert resp.status_code == 200, (role_key, resp.get_json())

    def test_viewer_and_assignee_cannot_update_list(self, client, role_matrix_world):
        for role_key in ("viewer", "assignee"):
            _login_as(client, role_matrix_world, role_key)
            resp = client.patch(f"/api/lists/{role_matrix_world['list'].id}", json={"title": "Should fail"})
            assert resp.status_code == 403, (role_key, resp.get_json())
