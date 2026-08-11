"""
Seed-скрипт для ручного и авто-тестирования ролевой модели в http-режиме
(Промпт 18). В отличие от app.auth.seed.seed_initial_users (который создаёт
только admin/user и вызывается автоматически при первом запуске), этот
скрипт запускается вручную и создаёт реалистичный набор данных:

  - 2 администратора (global_role=admin);
  - 3 обычных пользователя (global_role=user);
  - 3 списка с разными комбинациями ролей участников (owner/editor/
    assignee/viewer), включая список без доступа для одного из пользователей
    -- специально для проверки 403/404 на GET/PATCH/DELETE;
  - несколько задач в каждом списке (разные статусы/исполнители), чтобы
    сразу были данные для проверки view/edit/delete task по ролям.

Идемпотентен: повторный запуск не создаёт дублей -- если пользователь с
данным login уже есть, скрипт использует существующего вместо создания
нового (полезно, если seed_initial_users(app) уже отработал и в базе есть
admin/user из backend/app/auth/seed.py).

Запуск:

    cd backend
    source .venv/bin/activate
    export FLASK_ENV=development   # или testing/production -- база берётся
                                    # из соответствующего SQLALCHEMY_DATABASE_URI
    python seed_demo_data.py

После запуска пароли всех новых пользователей выводятся в консоль один раз
(они не хранятся в открытом виде, как и в app.auth.seed).
"""

import os
import secrets
import uuid
from datetime import datetime, timezone

from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import ListMembershipORM, ListORM, TaskORM, UserORM


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


DEMO_USERS = [
    {"login": "demo-admin1", "name": "Demo Admin 1", "email": "demo-admin1@todo-planner.local", "global_role": "admin"},
    {"login": "demo-admin2", "name": "Demo Admin 2", "email": "demo-admin2@todo-planner.local", "global_role": "admin"},
    {"login": "demo-alice", "name": "Alice (owner)", "email": "demo-alice@todo-planner.local", "global_role": "user"},
    {"login": "demo-bob", "name": "Bob (editor)", "email": "demo-bob@todo-planner.local", "global_role": "user"},
    {"login": "demo-carol", "name": "Carol (viewer/assignee)", "email": "demo-carol@todo-planner.local", "global_role": "user"},
]


def _get_or_create_user(spec, created_passwords):
    existing = UserORM.query.filter_by(login=spec["login"]).first()
    if existing:
        return existing

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
    db.session.flush()
    created_passwords.append((spec["login"], plain_password))
    return user


def _get_or_create_list(*, title, description=""):
    existing = ListORM.query.filter_by(title=title).first()
    if existing:
        return existing
    row = ListORM(
        id=str(uuid.uuid4()),
        title=title,
        description=description,
        color="#4f7cff",
        is_shared=True,
        default_view="list",
        settings="{}",
        archived=False,
        order_index=0,
        created_at=_now_iso(),
        updated_at=_now_iso(),
    )
    db.session.add(row)
    db.session.flush()
    return row


def _ensure_membership(*, list_id, user_id, role):
    existing = ListMembershipORM.query.filter_by(list_id=list_id, user_id=user_id).first()
    if existing:
        existing.role = role
        return existing
    row = ListMembershipORM(
        id=str(uuid.uuid4()), list_id=list_id, user_id=user_id, role=role, added_at=_now_iso(),
    )
    db.session.add(row)
    return row


def _ensure_task(*, list_id, title, created_by, assignee_id=None, status="open"):
    existing = TaskORM.query.filter_by(list_id=list_id, title=title).first()
    if existing:
        return existing
    timestamp = _now_iso()
    row = TaskORM(
        id=str(uuid.uuid4()),
        list_id=list_id,
        title=title,
        description="",
        status=status,
        priority="medium",
        assignee_id=assignee_id,
        created_by=created_by,
        updated_by=created_by,
        pinned=False,
        display_standalone=False,
        created_at=timestamp,
        updated_at=timestamp,
        last_activity_at=timestamp,
        completed_at=_now_iso() if status == "done" else None,
    )
    db.session.add(row)
    return row


def seed_demo_data(app):
    with app.app_context():
        created_passwords = []
        users = {spec["login"]: _get_or_create_user(spec, created_passwords) for spec in DEMO_USERS}
        db.session.commit()

        admin1 = users["demo-admin1"]
        admin2 = users["demo-admin2"]
        alice = users["demo-alice"]
        bob = users["demo-bob"]
        carol = users["demo-carol"]

        # Список 1: Alice -- owner, Bob -- editor, Carol -- viewer.
        list1 = _get_or_create_list(title="Demo: Marketing", description="Список для проверки owner/editor/viewer")
        _ensure_membership(list_id=list1.id, user_id=alice.id, role="owner")
        _ensure_membership(list_id=list1.id, user_id=bob.id, role="editor")
        _ensure_membership(list_id=list1.id, user_id=carol.id, role="viewer")
        _ensure_task(list_id=list1.id, title="Написать текст рассылки", created_by=alice.id, assignee_id=bob.id)
        _ensure_task(list_id=list1.id, title="Согласовать бюджет", created_by=alice.id, status="done")
        _ensure_task(list_id=list1.id, title="Проверить макет баннера", created_by=bob.id, assignee_id=carol.id)

        # Список 2: Bob -- owner, Carol -- assignee, Alice не состоит вовсе
        # (для проверки 403/404 у пользователя без доступа к списку).
        list2 = _get_or_create_list(title="Demo: Engineering", description="Список для проверки assignee и 403 у чужого пользователя")
        _ensure_membership(list_id=list2.id, user_id=bob.id, role="owner")
        _ensure_membership(list_id=list2.id, user_id=carol.id, role="assignee")
        _ensure_task(list_id=list2.id, title="Починить баг в API", created_by=bob.id, assignee_id=carol.id)
        _ensure_task(list_id=list2.id, title="Ревью пул-реквеста", created_by=bob.id, assignee_id=bob.id)

        # Список 3: Carol -- owner, Alice -- editor, Bob -- viewer.
        list3 = _get_or_create_list(title="Demo: Sales", description="Ещё одна комбинация ролей для регресс-тестов")
        _ensure_membership(list_id=list3.id, user_id=carol.id, role="owner")
        _ensure_membership(list_id=list3.id, user_id=alice.id, role="editor")
        _ensure_membership(list_id=list3.id, user_id=bob.id, role="viewer")
        _ensure_task(list_id=list3.id, title="Обзвонить лиды за неделю", created_by=carol.id, assignee_id=alice.id)

        db.session.commit()

        print("=" * 60)
        print("Todo Planner: seed-данные для ролевой модели готовы.")
        print(f"  Администраторы: {admin1.login}, {admin2.login}")
        print(f"  Обычные пользователи: {alice.login} (owner), {bob.login} (editor/owner), {carol.login} (viewer/assignee/owner)")
        print(f"  Списки: '{list1.title}', '{list2.title}' (без Alice), '{list3.title}'")
        if created_passwords:
            print("  Пароли новых пользователей (показываются только сейчас):")
            for login, plain_password in created_passwords:
                print(f"    login={login}  password={plain_password}")
        else:
            print("  Все demo-пользователи уже существовали -- новые пароли не создавались.")
        print("Сохраните эти пароли — повторно они не выводятся и не хранятся в открытом виде.")
        print("=" * 60)


if __name__ == "__main__":
    application = create_app(os.environ.get("FLASK_ENV", "development"))
    seed_demo_data(application)
