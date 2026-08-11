"""
Application factory. Backend спроектирован как реализация под уже
существующий frontend HTTP-слой (src/repositories/http/apiClient.js):
cookie-сессии + CSRF-заголовок, единый префикс /api, без JWT.
"""

from flask import Flask
from sqlalchemy import inspect

from config import get_config
from app.extensions import db, sess, cors, csrf, migrate

from app.health import health_bp
from app.auth import auth_bp
from app.users import users_bp
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

from app.auth.security import install_login_guard
from app.auth.seed import seed_initial_users


def create_app(config_name=None):
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    _register_extensions(app)
    _register_blueprints(app)
    install_login_guard(app)
    _bootstrap_database(app)

    return app


def _register_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    sess.init_app(app)
    csrf.init_app(app)
    cors.init_app(
        app,
        origins=app.config["CORS_ORIGINS"],
        supports_credentials=app.config["CORS_SUPPORTS_CREDENTIALS"],
    )


def _register_blueprints(app):
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
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
