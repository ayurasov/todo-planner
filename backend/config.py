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
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_SQLITE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'todo_planner.db')}"


class BaseConfig:
    """Общие настройки для всех окружений."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

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
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
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


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name=None):
    name = name or os.environ.get("FLASK_ENV", "development")
    return config_by_name.get(name, DevelopmentConfig)
