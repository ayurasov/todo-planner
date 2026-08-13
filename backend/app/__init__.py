"""
Application factory. Backend спроектирован как реализация под уже
существующий frontend HTTP-слой (src/repositories/http/apiClient.js):
cookie-сессии + CSRF-заголовок, единый префикс /api, без JWT.
"""

import logging
import sys

from flask import Flask, request
from sqlalchemy import inspect
from werkzeug.middleware.proxy_fix import ProxyFix

from config import get_config
from app.extensions import db, sess, cors, csrf, migrate, limiter

from app.health import health_bp
from app.auth import auth_bp
from app.users import users_bp
from app.departments import departments_bp
from app.lists import lists_bp
from app.tasks import tasks_bp
from app.meetings import meetings_bp
from app.recurrence import recurrence_bp
from app.history import history_bp
from app.notifications import notifications_bp
from app.saved_views import saved_views_bp
from app.comments import comments_bp
from app.checklists import checklists_bp
from app.notes import notes_bp
from app.analytics import analytics_bp
from app.uploads import uploads_bp

from app.auth.security import install_login_guard
from app.auth.seed import seed_initial_users


class _RequestContextFilter(logging.Filter):
    """Добавляет метод/путь запроса и id текущего пользователя к каждой
    log-записи, если она сделана внутри request-контекста (вне
    контекста -- пустые значения, без исключений).
    """

    def filter(self, record):  # noqa: A003
        from flask import has_request_context, session

        if has_request_context():
            record.method = request.method
            record.path = request.path
            record.remote_addr = request.headers.get("X-Forwarded-For", request.remote_addr)
            record.user_id = session.get("user_id") if session else None
        else:
            record.method = None
            record.path = None
            record.remote_addr = None
            record.user_id = None
        return True


class _JsonLogFormatter(logging.Formatter):
    """Структурированный (JSON-line) вывод вместо print()/текстовых тресбеков,
    чтобы логи можно было парсить/агрегировать (docker logs -> journald/ELK/Loki
    и т.п.) без regex-эвристик.
    """

    def format(self, record):
        import json
        import datetime

        payload = {
            "timestamp": datetime.datetime.fromtimestamp(
                record.created, tz=datetime.timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "method": getattr(record, "method", None),
            "path": getattr(record, "path", None),
            "remote_addr": getattr(record, "remote_addr", None),
            "user_id": getattr(record, "user_id", None),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def _configure_logging(app):
    """Заменяет дефолтное Flask/Werkzeug-логирование (и возможные print())
    на структурированный JSON-вывод в stdout -- тоесть, как ожидается от
    container-приложений (docker/nginx logs -> journald/агрегатор), без зависимости
    от файловой системы внутри контейнера.
    """

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(_JsonLogFormatter())
    handler.addFilter(_RequestContextFilter())

    app.logger.handlers = [handler]
    app.logger.setLevel(logging.DEBUG if app.config.get("DEBUG") else logging.INFO)
    app.logger.propagate = False

    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.handlers = [handler]
    werkzeug_logger.propagate = False

    @app.errorhandler(Exception)
    def _log_unhandled_exception(exc):  # noqa: WPS430
        app.logger.exception("Unhandled exception during request")
        # Без rollback() сессия SQLAlchemy остаётся «грязной» после любой ошибки
        # (IntegrityError, CSRFError и т.п.): невыполненные insert/update продолжают
        # висеть в Session на этом gunicorn-воркере и портят транзакцию следующего,
        # ни в чём не повинного запроса на том же воркере (например, INSERT списка
        # после отклонённого CSRF-запроса). db.session.remove() откатывает и
        # выбрасывает scoped session, гарантируя чистое состояние для следующего запроса.
        db.session.remove()
        raise exc


def create_app(config_name=None, skip_bootstrap=False):
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    _configure_logging(app)

    if app.config.get("ENV") == "production":
        # nginx reverse-proxy передаёт X-Forwarded-For/-Proto -- ProxyFix восстанавливает
        # реальный remote_addr/scheme, иначе rate limiting (Flask-Limiter) и аудит-логи стали
        # бы видеть только IP nginx-контейнера.
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    _register_extensions(app)
    _register_blueprints(app)
    install_login_guard(app)

    if not skip_bootstrap:
        _bootstrap_database(app)

    return app


def _register_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    sess.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    cors.init_app(
        app,
        origins=app.config["CORS_ORIGINS"],
        supports_credentials=app.config["CORS_SUPPORTS_CREDENTIALS"],
    )


def _register_blueprints(app):
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(departments_bp)
    app.register_blueprint(lists_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(meetings_bp)
    app.register_blueprint(recurrence_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(saved_views_bp)
    app.register_blueprint(comments_bp)
    app.register_blueprint(checklists_bp)
    app.register_blueprint(notes_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(uploads_bp)


def _bootstrap_database(app):
    """Для testing по-прежнему поднимаем схему автоматически в in-memory SQLite.
    Для development/production схема должна управляться Alembic-миграциями.
    Начальных пользователей сидим только если таблица users уже существует.
    """

    with app.app_context():
        if app.config.get("TESTING"):
            db.create_all()
            seed_initial_users(app)
            return

        inspector = inspect(db.engine)
        if "users" in inspector.get_table_names():
            seed_initial_users(app)
            return

        app.logger.warning(
            "База данных ещё не инициализирована. Выполните 'alembic upgrade head' перед запуском приложения."
        )
