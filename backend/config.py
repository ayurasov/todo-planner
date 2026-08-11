"""
Конфигурация Flask-приложения. три профиля (development/testing/production)
подобраны под уже существующий frontend apiClient.js:
- cookie-based сессии (credentials: 'include'), без JWT;
- CSRF-заголовок 'X-CSRF-Token', который apiClient проставляет для не-GET
  запросов (см. src/repositories/http/apiClient.js). Добавлен также 'X-CSRFToken'
  (стандартный заголовок из рекомендаций Flask-WTF для AJAX-клиентов) для
  совместимости с будущими клиентами;
- BASE_URL фронтенда = '/api' -> весь URL-space backend строится под этим
  префиксом на уровне blueprints, а не здесь.

Промпт 23 (security review): production-профиль больше не допускает дефолтный
секрет -- отсутствие SECRET_KEY в окружении валит старт приложения с явной
ошибкой (fail-fast), а не тихо работает на предсказуемом значении.
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_SQLITE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'todo_planner.db')}"

_INSECURE_DEV_SECRET_KEY = "dev-secret-key"


class BaseConfig:
    """Общие настройки для всех окружений."""

    SECRET_KEY = os.environ.get("SECRET_KEY", _INSECURE_DEV_SECRET_KEY)

    DATABASE_URL = os.environ.get("DATABASE_URL")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "SQLALCHEMY_DATABASE_URI",
        DATABASE_URL or DEFAULT_SQLITE_URI,
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }

    SESSION_TYPE = os.environ.get("SESSION_TYPE", "filesystem")
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_FILE_DIR = os.path.join(BASE_DIR, ".flask_session")
    SESSION_COOKIE_NAME = "todo_planner_session"
    # HttpOnly -- cookie недоступна из JS (защита от XSS-кражи сессии).
    SESSION_COOKIE_HTTPONLY = True
    # Lax -- баланс между CSRF-защитой и обычными top-level GET-переходами;
    # может быть переопределен через SESSION_COOKIE_SAMESITE env, если frontend и backend
    # разнесены по разным origin и нужен 'None' (тогда обязателен Secure=True + HTTPS).
    SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = False

    WTF_CSRF_ENABLED = True
    WTF_CSRF_HEADERS = ["X-CSRF-Token", "X-CSRFToken"]
    WTF_CSRF_TIME_LIMIT = None
    WTF_CSRF_SSL_STRICT = False

    CORS_ORIGINS = [
        origin.strip()
        for origin in os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173").split(",")
        if origin.strip()
    ]
    CORS_SUPPORTS_CREDENTIALS = True

    # Rate limiting (Flask-Limiter) -- защита /api/auth/login от brute-force.
    # Файловый storage подходит для single-instance deployment; для multi-worker/
    # multi-instance production ставьте RATELIMIT_STORAGE_URI=redis://... (Flask-Limiter
    # поддерживает это из коробки, добавление Redis в docker-compose -- отдельный шаг).
    RATELIMIT_ENABLED = os.environ.get("RATELIMIT_ENABLED", "true").lower() != "false"
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_DEFAULT = None
    RATELIMIT_HEADERS_ENABLED = True
    # /api/auth/login: не более 10 попыток в минуту и 50 в час с одного IP.
    LOGIN_RATE_LIMIT = os.environ.get("LOGIN_RATE_LIMIT", "10 per minute;50 per hour")


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    ENV = "development"


class TestingConfig(BaseConfig):
    TESTING = True
    ENV = "testing"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}
    WTF_CSRF_ENABLED = False
    SESSION_TYPE = "filesystem"
    SESSION_FILE_DIR = os.path.join(BASE_DIR, ".flask_session_test")
    RATELIMIT_ENABLED = False


class ProductionConfig(BaseConfig):
    DEBUG = False
    ENV = "production"
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_SSL_STRICT = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
        "pool_size": int(os.environ.get("DB_POOL_SIZE", "5")),
        "max_overflow": int(os.environ.get("DB_MAX_OVERFLOW", "5")),
    }

    def __init__(self):
        raise RuntimeError("ProductionConfig используется как класс, не инстанцируется")


def _require_production_secret_key():
    """Fail-fast: в production запрещён дефолтный/пустой SECRET_KEY.
    Без этой проверки приложение тихо стартовало бы с предсказуемым секретом,
    что ломает безопасность сессий и CSRF-токенов.
    """

    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key or secret_key == _INSECURE_DEV_SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY не задан (или используется дефолтное insecure-значение). "
            "Для FLASK_ENV=production обязательно установите переменную окружения "
            "SECRET_KEY на длинную случайную строку (например, "
            "`python -c 'import secrets; print(secrets.token_hex(32))'`) перед запуском."
        )


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name=None):
    name = name or os.environ.get("FLASK_ENV", "development")
    if name == "production":
        _require_production_secret_key()
    return config_by_name.get(name, DevelopmentConfig)
