"""
Авторизационный middleware backend v2: cookie-based server-side сессии
(Flask-Session), без JWT/localStorage. Кладёт в `session["user_id"]` id
авторизованного пользователя.

Формат ошибок стабилен и рассчитан на сопоставление на фронтенде с
`AuthRequiredError`/`PermissionDeniedError` (src/repositories/http/apiClient.js),
которые различают ответы только по HTTP-статусу (401 / 403), но тело ответа
всегда содержит `{"error": "<code>", "message": "<text>"}`, чтобы будущие
`http`-репозитории могли надёжно читать `payload.error`/`payload.message`.
"""

from functools import wraps

from flask import jsonify, session, request


# Полные имена Flask-endpoint'ов ("<blueprint>.<view>"), которые доступны без
# аутентификации: health-check, сам логин и выдача CSRF-токена (он нужен
# до того, как появится сессия -- фронтенд запрашивает его перед login).
EXEMPT_ENDPOINTS = {
    "health.health",
    "auth.login",
    "auth.get_csrf_token",
}


def auth_error_response(code: str, message: str, status: int):
    return jsonify({"error": code, "message": message}), status


def is_authenticated() -> bool:
    return "user_id" in session


def current_user_id():
    return session.get("user_id")


def login_required(view):
    """Декоратор для явной защиты отдельного view (если не хватает
    глобального `install_login_guard`). Отдаёт 401 в том же формате, что и
    глобальный guard.
    """

    @wraps(view)
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            return auth_error_response("auth_required", "Требуется авторизация", 401)
        return view(*args, **kwargs)

    return wrapper


def install_login_guard(app):
    """Глобальный `before_request`-guard — применяется ко всем зарегистрированным
    blueprint routes без того, чтобы навешивать `@login_required` на каждый
    из уже созданных заглушечных route'ов. Исключения -- `EXEMPT_ENDPOINTS`
    и любые CORS-preflight (`OPTIONS`) запросы.
    """

    @app.before_request
    def _enforce_login():  # noqa: WPS430
        if request.method == "OPTIONS":
            return None
        endpoint = request.endpoint
        if endpoint is None or endpoint in EXEMPT_ENDPOINTS or endpoint == "static":
            return None
        if not is_authenticated():
            return auth_error_response("auth_required", "Требуется авторизация", 401)
        return None
