"""
Промпт 20: unit/integration-тесты auth flow.
Промпт 23: тесты POST /api/auth/change-password.

Покрывает:
- POST /api/auth/login (успех/неверный пароль/неактивный пользователь/невалидный payload)
- POST /api/auth/logout
- GET /api/auth/me (авторизован/не авторизован)
- GET /api/auth/csrf-token и CSRF-защиту mutating-запросов, когда
  WTF_CSRF_ENABLED включён явно для этого модуля (в остальных тестах
  проекта CSRF отключён через TestingConfig, чтобы не усложнять фикстуры
  ролевой матрицы).
- POST /api/auth/change-password (успешная смена, неверный текущий пароль,
  без авторизации, слишком короткий новый пароль, вход под новым паролем после смены).
"""

from tests.conftest import PASSWORD, make_user


class TestLogin:
    def test_login_with_valid_credentials_returns_user_dto(self, client, app):
        with app.app_context():
            make_user(login="auth-user")

        resp = client.post("/api/auth/login", json={"login": "auth-user", "password": PASSWORD})

        assert resp.status_code == 200
        body = resp.get_json()
        assert "user" in body
        user = body["user"]
        assert user["id"]
        assert user["name"] == "auth-user"
        assert "globalRole" in user
        assert "isActive" in user

    def test_login_with_wrong_password_returns_401(self, client, app):
        with app.app_context():
            make_user(login="auth-user2")

        resp = client.post("/api/auth/login", json={"login": "auth-user2", "password": "wrong-password"})

        assert resp.status_code == 401
        assert resp.get_json()["error"] == "invalid_credentials"

    def test_login_with_unknown_login_returns_401(self, client):
        resp = client.post("/api/auth/login", json={"login": "no-such-user", "password": PASSWORD})
        assert resp.status_code == 401
        assert resp.get_json()["error"] == "invalid_credentials"

    def test_login_missing_fields_returns_401(self, client):
        resp = client.post("/api/auth/login", json={})
        assert resp.status_code == 401

    def test_login_disabled_account_returns_403(self, client, app):
        with app.app_context():
            make_user(login="disabled-user", is_active=False)

        resp = client.post("/api/auth/login", json={"login": "disabled-user", "password": PASSWORD})

        assert resp.status_code == 403
        assert resp.get_json()["error"] == "account_disabled"


class TestLogout:
    def test_logout_clears_session(self, client, app):
        with app.app_context():
            make_user(login="logout-user")

        client.post("/api/auth/login", json={"login": "logout-user", "password": PASSWORD})
        resp = client.post("/api/auth/logout")
        assert resp.status_code == 200

        me_resp = client.get("/api/auth/me")
        assert me_resp.status_code == 401


class TestMe:
    def test_me_requires_authentication(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401
        assert resp.get_json()["error"] == "auth_required"

    def test_me_returns_current_user_after_login(self, client, app):
        with app.app_context():
            make_user(login="me-user")

        client.post("/api/auth/login", json={"login": "me-user", "password": PASSWORD})
        resp = client.get("/api/auth/me")

        assert resp.status_code == 200
        assert resp.get_json()["name"] == "me-user"

    def test_protected_endpoint_requires_login(self, client):
        resp = client.get("/api/lists")
        assert resp.status_code == 401
        assert resp.get_json()["error"] == "auth_required"


class TestCsrfToken:
    def test_csrf_token_endpoint_is_public_and_returns_token(self, client):
        resp = client.get("/api/auth/csrf-token")
        assert resp.status_code == 200
        assert "csrfToken" in resp.get_json()

    def test_mutating_request_without_csrf_token_is_rejected(self, csrf_client, csrf_app):
        with csrf_app.app_context():
            make_user(login="csrf-user")

        token = csrf_client.get("/api/auth/csrf-token").get_json()["csrfToken"]
        login_resp = csrf_client.post(
            "/api/auth/login",
            json={"login": "csrf-user", "password": PASSWORD},
            headers={"X-CSRF-Token": token},
        )
        assert login_resp.status_code == 200

        resp = csrf_client.post("/api/tasks", json={"title": "no csrf token"})
        assert resp.status_code == 400

    def test_mutating_request_with_valid_csrf_token_succeeds(self, csrf_client, csrf_app):
        with csrf_app.app_context():
            make_user(login="csrf-user2")

        pre_login_token = csrf_client.get("/api/auth/csrf-token").get_json()["csrfToken"]
        csrf_client.post(
            "/api/auth/login",
            json={"login": "csrf-user2", "password": PASSWORD},
            headers={"X-CSRF-Token": pre_login_token},
        )
        post_login_token = csrf_client.get("/api/auth/csrf-token").get_json()["csrfToken"]

        resp = csrf_client.post(
            "/api/tasks",
            json={"title": "with csrf token"},
            headers={"X-CSRF-Token": post_login_token},
        )
        assert resp.status_code == 201


class TestChangePassword:
    def test_requires_authentication(self, client):
        resp = client.post(
            "/api/auth/change-password",
            json={"currentPassword": PASSWORD, "newPassword": "a-new-strong-password"},
        )
        assert resp.status_code == 401
        assert resp.get_json()["error"] == "auth_required"

    def test_wrong_current_password_returns_401(self, client, app):
        with app.app_context():
            make_user(login="cp-user1")

        client.post("/api/auth/login", json={"login": "cp-user1", "password": PASSWORD})
        resp = client.post(
            "/api/auth/change-password",
            json={"currentPassword": "totally-wrong", "newPassword": "a-new-strong-password"},
        )
        assert resp.status_code == 401
        assert resp.get_json()["error"] == "invalid_credentials"

    def test_new_password_too_short_returns_400(self, client, app):
        with app.app_context():
            make_user(login="cp-user2")

        client.post("/api/auth/login", json={"login": "cp-user2", "password": PASSWORD})
        resp = client.post(
            "/api/auth/change-password",
            json={"currentPassword": PASSWORD, "newPassword": "short"},
        )
        assert resp.status_code == 400
        assert resp.get_json()["error"] == "validation_error"

    def test_successful_change_allows_login_with_new_password(self, client, app):
        with app.app_context():
            make_user(login="cp-user3")

        client.post("/api/auth/login", json={"login": "cp-user3", "password": PASSWORD})
        resp = client.post(
            "/api/auth/change-password",
            json={"currentPassword": PASSWORD, "newPassword": "a-new-strong-password"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "password_changed"

        client.post("/api/auth/logout")

        old_password_resp = client.post(
            "/api/auth/login", json={"login": "cp-user3", "password": PASSWORD}
        )
        assert old_password_resp.status_code == 401

        new_password_resp = client.post(
            "/api/auth/login", json={"login": "cp-user3", "password": "a-new-strong-password"}
        )
        assert new_password_resp.status_code == 200
