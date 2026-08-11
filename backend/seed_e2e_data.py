"""
Seed-скрипт с детерминированными учётными записями для Playwright E2E-тестов (Промпт 24).

В отличие от seed_demo_data.py (где пароли случайные и печатаются только в лог один раз),
здесь пароли фиксированы (из кода или env), чтобы Playwright мог входить без
разбора логов backend. Скрипт предназначен **только для CI/staging окружения**
(предназначенный для e2e docker-compose стека из Промпта 22, не для production) --
сознательно отказывает запуск в FLASK_ENV=production.

Запуск:

    cd backend
    export FLASK_ENV=testing   # или development -- никогда production
    python seed_e2e_data.py

Идемпотентен, переиспользует seed_demo_data._get_or_create_user и аналогичные хелперы.
"""

import os
import uuid
from datetime import datetime, timezone

from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import UserORM

E2E_PASSWORD = os.environ.get("E2E_SEED_PASSWORD", "E2E-test-pass-123!")

E2E_USERS = [
    {"login": "e2e-admin", "name": "E2E Admin", "email": "e2e-admin@todo-planner.local", "global_role": "admin"},
    {"login": "e2e-owner", "name": "E2E Owner", "email": "e2e-owner@todo-planner.local", "global_role": "user"},
    {"login": "e2e-viewer", "name": "E2E Viewer", "email": "e2e-viewer@todo-planner.local", "global_role": "user"},
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _get_or_create_e2e_user(spec):
    existing = UserORM.query.filter_by(login=spec["login"]).first()
    if existing:
        existing.password_hash = generate_password_hash(E2E_PASSWORD)
        existing.is_active = True
        return existing
    user = UserORM(
        id=str(uuid.uuid4()),
        name=spec["name"],
        email=spec["email"],
        login=spec["login"],
        password_hash=generate_password_hash(E2E_PASSWORD),
        timezone="Europe/Moscow",
        global_role=spec["global_role"],
        is_active=True,
        created_at=_now_iso(),
        updated_at=_now_iso(),
    )
    db.session.add(user)
    return user


def seed_e2e_data(app):
    if app.config.get("ENV") == "production" or os.environ.get("FLASK_ENV") == "production":
        raise RuntimeError("seed_e2e_data.py запрещён в FLASK_ENV=production (детерминированные пароли -- только для CI/staging)")

    with app.app_context():
        from app.models import ListMembershipORM, ListORM

        users = {spec["login"]: _get_or_create_e2e_user(spec) for spec in E2E_USERS}
        db.session.commit()

        owner = users["e2e-owner"]
        viewer = users["e2e-viewer"]

        e2e_list = ListORM.query.filter_by(title="E2E: Smoke").first()
        if not e2e_list:
            e2e_list = ListORM(
                id=str(uuid.uuid4()), title="E2E: Smoke", description="список для Playwright smoke-тестов",
                color="#4f7cff", is_shared=True, default_view="list", settings="{}", archived=False,
                order_index=0, created_at=_now_iso(), updated_at=_now_iso(),
            )
            db.session.add(e2e_list)
            db.session.flush()

        for user, role in ((owner, "owner"), (viewer, "viewer")):
            existing = ListMembershipORM.query.filter_by(list_id=e2e_list.id, user_id=user.id).first()
            if not existing:
                db.session.add(ListMembershipORM(
                    id=str(uuid.uuid4()), list_id=e2e_list.id, user_id=user.id, role=role, added_at=_now_iso(),
                ))

        db.session.commit()

        print("=" * 60)
        print("Todo Planner: E2E seed-данные готовы (только для CI/staging).")
        print(f"  Пользователи: e2e-admin, e2e-owner, e2e-viewer; пароль у всех одинаковая (E2E_SEED_PASSWORD).")
        print(f"  Список: '{e2e_list.title}' (e2e-owner=owner, e2e-viewer=viewer).")
        print("=" * 60)


if __name__ == "__main__":
    application = create_app(os.environ.get("FLASK_ENV", "testing"))
    seed_e2e_data(application)
