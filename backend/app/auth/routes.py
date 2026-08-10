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
"""

from flask import jsonify, request, session
from flask_wtf.csrf import generate_csrf
from pydantic import ValidationError
from werkzeug.security import check_password_hash

from app.auth import auth_bp
from app.auth.security import auth_error_response, current_user_id, login_required
from app.dto import LoginRequestDTO, LoginResponseDTO
from app.mappers import orm_to_domain, domain_to_dto
from app.models import UserORM


@auth_bp.route("/login", methods=["POST"])
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

    session.clear()
    session["user_id"] = user_orm.id
    session.permanent = False

    user = orm_to_domain.user(user_orm)
    dto = domain_to_dto.user(user)
    return jsonify(LoginResponseDTO(user=dto).model_dump(by_alias=True))


@auth_bp.route("/logout", methods=["POST"])
def logout(**kwargs):
    session.clear()
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
