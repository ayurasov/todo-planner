"""
Аутентификация blueprint 'auth' под уже существующий frontend
src/repositories/http/apiClient.js:
  - cookie-based server-side сессии (Flask-Session, credentials: 'include'),
    без JWT/localStorage;
  - CSRF-защита через Flask-WTF CSRFProtect, токен передаётся AJAX-клиентом
    в заголовке X-CSRF-Token (apiClient.js) -- см. WTF_CSRF_HEADERS в config.py;
  - стабильный формат ошибки {"error": <code>, "message": <text>} для 401/403,
    чтобы будущий http-репозиторий мог надёжно сопоставить его с
    AuthRequiredError/PermissionDeniedError.

ORM -> domain -> DTO проток использует уже существующий слой
(app.models / app.mappers / app.dto), созданный в Промпте 10.

Промпт 23 (security review): на login навешен rate limit (Flask-Limiter,
settings.LOGIN_RATE_LIMIT) -- защита от brute-force подбора пароля по IP.
Добавлен POST /api/auth/change-password для залогиненного пользователя --
до этого пароли только генерировались при bootstrap (seed_initial_users) и
печатались в лог один раз, без возможности самостоятельно сменить их.
"""

from flask import current_app, jsonify, request, session
from flask_wtf.csrf import generate_csrf
from pydantic import ValidationError
from werkzeug.security import check_password_hash, generate_password_hash

from app.auth import auth_bp
from app.auth.security import auth_error_response, current_user_id, login_required
from app.dto import ChangePasswordRequestDTO, LoginRequestDTO, LoginResponseDTO
from app.extensions import db, limiter
from app.mappers import orm_to_domain, domain_to_dto
from app.models import UserORM


def _login_rate_limit():
    return current_app.config.get("LOGIN_RATE_LIMIT", "10 per minute;50 per hour")


@auth_bp.route("/login", methods=["POST"])
@limiter.limit(_login_rate_limit)
def login(**kwargs):
    try:
        payload = LoginRequestDTO.model_validate(request.get_json(silent=True) or {})
    except ValidationError:
        return auth_error_response("invalid_credentials", "Неверный login или пароль", 401)

    user_orm = UserORM.query.filter_by(login=payload.login).first()

    if user_orm is None or not user_orm.password_hash or not check_password_hash(
        user_orm.password_hash, payload.password
    ):
        return auth_error_response("invalid_credentials", "Неверный login или пароль", 401)

    if not user_orm.is_active:
        return auth_error_response("account_disabled", "Аккаунт деактивирован", 403)

    # session.clear() стирает весь Flask-Session, включая csrf_token, который был
    # выдан фронтенду раньше через GET /api/auth/csrf-token и уже сохранён в
    # apiClient.js/памяти клиента. Если не восстановить его, следующий же
    # не-GET запрос (тот же токен в заголовке X-CSRF-Token) не найдёт токен в
    # свежей сессии и упадёт с CSRFError "session token is missing" (см. баг
    # "не могу ничего создать после логина").
    csrf_token = session.get("csrf_token")
    session.clear()
    if csrf_token is not None:
        session["csrf_token"] = csrf_token
    session["user_id"] = user_orm.id
    session.permanent = False

    user = orm_to_domain.user(user_orm)
    dto = domain_to_dto.user(user)
    return jsonify(LoginResponseDTO(user=dto).model_dump(by_alias=True))


@auth_bp.route("/logout", methods=["POST"])
def logout(**kwargs):
    # Сохраняем csrf_token по той же причине, что и в login() -- иначе следующий
    # logout/login в той же вкладке (без обновления страницы) снова потеряет
    # CSRF-сессию для уже сохранённого на фронтенде токена.
    csrf_token = session.get("csrf_token")
    session.clear()
    if csrf_token is not None:
        session["csrf_token"] = csrf_token
    return jsonify({"message": "logged_out"})


@auth_bp.route("/me", methods=["GET"])
@login_required
def get_current_user(**kwargs):
    user_orm = UserORM.query.get(current_user_id())

    if user_orm is None or not user_orm.is_active:
        session.clear()
        return auth_error_response("auth_required", "Требуется авторизация", 401)

    user = orm_to_domain.user(user_orm)
    dto = domain_to_dto.user(user)
    return jsonify(dto.model_dump(by_alias=True))


@auth_bp.route("/csrf-token", methods=["GET"])
def get_csrf_token(**kwargs):
    return jsonify({"csrfToken": generate_csrf()})


@auth_bp.route("/change-password", methods=["POST"])
@login_required
def change_password(**kwargs):
    """Смена пароля для текущего авторизованного пользователя.
    Принимает { "currentPassword": ..., "newPassword": ... }, требует правильный
    текущий пароль (защита от сценария "угнанная/оставленная сессия"), `newPassword`
    должен быть не короце 8 символов (валидация в ChangePasswordRequestDTO).
    Сбрасывает все другие сессии этого браузера не требуется -- Flask-Session
    не хранит список активных сессий на пользователя (out of scope этого шага).
    """

    try:
        payload = ChangePasswordRequestDTO.model_validate(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "details": exc.errors()}), 400

    user_orm = UserORM.query.get(current_user_id())
    if user_orm is None or not user_orm.is_active:
        session.clear()
        return auth_error_response("auth_required", "Требуется авторизация", 401)

    if not user_orm.password_hash or not check_password_hash(
        user_orm.password_hash, payload.current_password
    ):
        return auth_error_response("invalid_credentials", "Текущий пароль указан неверно", 401)

    user_orm.password_hash = generate_password_hash(payload.new_password)
    db.session.commit()

    return jsonify({"message": "password_changed"})
