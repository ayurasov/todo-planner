"""
Тесты для isSystem-флага и GET /api/users/admin/all endpoint.

Проверяем:
  1. GET /api/users не возвращает системных пользователей (даже админу).
  2. GET /api/users/admin/all возвращает всех включая isSystem=True.
  3. GET /api/users/admin/all запрещён не-админу (403).
  4. PATCH /api/users/:id с {isSystem: true} работает только для admin.
  5. DTO-контракт /api/users/admin/all содержит isSystem.
"""
from tests.conftest import PASSWORD, make_user, login


class TestIsSystemFlag:
    def test_get_users_excludes_system_users(self, client, app):
        with app.app_context():
            admin = make_user(login="sys-admin-1", global_role="admin")
            sys_user = make_user(login="sys-system-1")
            # Назначаем is_system напрямую через ORM
            from app.extensions import db
            sys_user.is_system = True
            db.session.commit()
            admin_id = admin.id
            sys_id = sys_user.id

        login(client, admin)

        resp = client.get("/api/users")
        assert resp.status_code == 200
        ids = [u["id"] for u in resp.get_json()]
        assert sys_id not in ids, "GET /api/users не должен возвращать системных"
        assert admin_id in ids

    def test_admin_all_includes_system_users(self, client, app):
        with app.app_context():
            admin = make_user(login="sys-admin-2", global_role="admin")
            sys_user = make_user(login="sys-system-2")
            from app.extensions import db
            sys_user.is_system = True
            db.session.commit()
            sys_id = sys_user.id

        login(client, admin)

        resp = client.get("/api/users/admin/all")
        assert resp.status_code == 200
        ids = [u["id"] for u in resp.get_json()]
        assert sys_id in ids, "GET /api/users/admin/all должен возвращать системных"

    def test_admin_all_forbidden_for_non_admin(self, client, app):
        with app.app_context():
            regular = make_user(login="sys-regular-1", global_role="user")

        login(client, regular)

        resp = client.get("/api/users/admin/all")
        assert resp.status_code == 403

    def test_patch_is_system_requires_admin(self, client, app):
        """PATCH isSystem должен быть заблокирован для обычного пользователя (403)."""
        with app.app_context():
            regular = make_user(login="sys-regular-2", global_role="user")
            target = make_user(login="sys-target-1")
            target_id = target.id

        login(client, regular)

        resp = client.patch(f"/api/users/{target_id}", json={"isSystem": True})
        assert resp.status_code == 403

    def test_admin_can_set_is_system_flag(self, client, app):
        """Admin может выставить isSystem=True; DTO содержит isSystem в camelCase."""
        with app.app_context():
            admin = make_user(login="sys-admin-3", global_role="admin")
            target = make_user(login="sys-target-2")
            target_id = target.id

        login(client, admin)

        resp = client.patch(f"/api/users/{target_id}", json={"isSystem": True})
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["isSystem"] is True, "DTO должен содержать isSystem"
        assert "is_system" not in body, "DTO не должен содержать snake_case is_system"

    def test_admin_can_unset_is_system_flag(self, client, app):
        """Admin может снять isSystem."""
        with app.app_context():
            admin = make_user(login="sys-admin-4", global_role="admin")
            from app.extensions import db
            sys_user = make_user(login="sys-target-3")
            sys_user.is_system = True
            db.session.commit()
            sys_id = sys_user.id

        login(client, admin)

        resp = client.patch(f"/api/users/{sys_id}", json={"isSystem": False})
        assert resp.status_code == 200
        assert resp.get_json()["isSystem"] is False
