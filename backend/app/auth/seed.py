"""
Bootstrap-логика для нагальных пользователей (применяется, если таблица
`users` пуста). Пароли генерируются случайно, хешируются через werkzeug
(`password_hash`) и в базе никогда не хранятся в открытом виде. Открытый текст
паролявывыводится в лог ровно один раз -- в момент создания,
второй запуск приложения ничего не найдёт и ничего не выведет.

Заметка (Промпт 23): вывод идёт через `app.logger.warning`, а не `print()`, чтобы
попасть в единый структурированный (JSON) лог контейнера (см. app/__init__.py)
-- но открытый текст пароля всё ещё будет виден ровно один раз.

Структура пользователей совпадает с таблицей `users`
(backend/migrations/001_create_users.up.sql) и domain/entities.User
(`global_role` ∈ {"admin", "user"}).
"""

import secrets
import uuid
from datetime import datetime, timezone

from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import UserORM

SEED_USERS = [
    {"login": "admin", "name": "Admin", "email": "admin@todo-planner.local", "global_role": "admin"},
    {"login": "user", "name": "User", "email": "user@todo-planner.local", "global_role": "user"},
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def seed_initial_users(app):
    """Создаёт начальных пользователей, если таблица users пуста.
    Вызывается один раз внутри app-контекста (см. app/__init__.py).
    """

    with app.app_context():
        if UserORM.query.count() > 0:
            return

        created = []
        for spec in SEED_USERS:
            plain_password = secrets.token_urlsafe(9)
            user = UserORM(
                id=str(uuid.uuid4()),
                name=spec["name"],
                email=spec["email"],
                login=spec["login"],
                password_hash=generate_password_hash(plain_password),
                timezone="Europe/Moscow",
                global_role=spec["global_role"],
                is_active=True,
                created_at=_now_iso(),
                updated_at=_now_iso(),
            )
            db.session.add(user)
            created.append((spec["login"], plain_password))

        db.session.commit()

        lines = [
            "Todo Planner: созданы начальные пользователи (пароли показываются только сейчас):",
        ]
        for login, plain_password in created:
            lines.append(f"  login={login}  password={plain_password}")
        lines.append("Сохраните эти пароли — повторно они не выводятся и не хранятся в открытом виде.")
        app.logger.warning("\n".join(lines))
