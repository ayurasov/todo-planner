"""
Общие фикстуры для integration-тестов ролевой модели (Промпт 18).

Поднимает Flask test client поверх in-memory SQLite (config.TestingConfig,
WTF_CSRF_ENABLED=False), создаёт пользователей/списки/задачи напрямую через
ORM (без прохождения auth-роутов) и логинит нужного пользователя через
POST /api/auth/login перед каждым запросом теста.
"""

import uuid
from datetime import datetime, timezone

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import ListMembershipORM, ListORM, TaskORM, UserORM


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


@pytest.fixture()
def app():
    application = create_app("testing")
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db_session(app):
    with app.app_context():
        yield db.session


@pytest.fixture()
def csrf_app():
    """Отдельное приложение с включённым WTF_CSRF_ENABLED поверх testing-профиля,
    чтобы явно проверить CSRF-защиту mutating-запросов (в остальных тестах
    CSRF отключён через TestingConfig ради простоты фикстур ролевой матрицы)."""
    application = create_app("testing")
    application.config["WTF_CSRF_ENABLED"] = True
    yield application


@pytest.fixture()
def csrf_client(csrf_app):
    with csrf_app.app_context():
        db.create_all()
    return csrf_app.test_client()


PASSWORD = "test-password-123"


def make_user(*, login, global_role="user", is_active=True):
    user = UserORM(
        id=str(uuid.uuid4()),
        name=login,
        email=f"{login}@example.test",
        login=login,
        password_hash=generate_password_hash(PASSWORD),
        timezone="Europe/Moscow",
        global_role=global_role,
        is_active=is_active,
        created_at=_now_iso(),
        updated_at=_now_iso(),
    )
    db.session.add(user)
    db.session.commit()
    return user


def make_list(*, title="List"):
    row = ListORM(
        id=str(uuid.uuid4()),
        title=title,
        description="",
        color="#4f7cff",
        is_shared=False,
        default_view="list",
        settings="{}",
        archived=False,
        order_index=0,
        created_at=_now_iso(),
        updated_at=_now_iso(),
    )
    db.session.add(row)
    db.session.commit()
    return row


def add_membership(*, list_id, user_id, role):
    row = ListMembershipORM(
        id=str(uuid.uuid4()), list_id=list_id, user_id=user_id, role=role, added_at=_now_iso(),
    )
    db.session.add(row)
    db.session.commit()
    return row


def make_task(*, list_id=None, title="Task", created_by=None, assignee_id=None, status="open"):
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
        completed_at=None,
    )
    db.session.add(row)
    db.session.commit()
    return row


@pytest.fixture()
def role_matrix_world(app):
    """Единый мир для матрицы ролей: 1 список с owner/editor/viewer/assignee-
    участниками + пользователь без доступа + global admin, плюс по одной
    задаче списка, созданной owner'ом и назначенной на editor.
    """
    with app.app_context():
        admin = make_user(login="rm-admin", global_role="admin")
        owner = make_user(login="rm-owner")
        editor = make_user(login="rm-editor")
        viewer = make_user(login="rm-viewer")
        assignee = make_user(login="rm-assignee")
        outsider = make_user(login="rm-outsider")

        todo_list = make_list(title="Role matrix list")
        add_membership(list_id=todo_list.id, user_id=owner.id, role="owner")
        add_membership(list_id=todo_list.id, user_id=editor.id, role="editor")
        add_membership(list_id=todo_list.id, user_id=viewer.id, role="viewer")
        add_membership(list_id=todo_list.id, user_id=assignee.id, role="assignee")

        task = make_task(list_id=todo_list.id, title="List task", created_by=owner.id, assignee_id=editor.id)

        yield {
            "admin": admin,
            "owner": owner,
            "editor": editor,
            "viewer": viewer,
            "assignee": assignee,
            "outsider": outsider,
            "list": todo_list,
            "task": task,
        }


def login(client, user):
    resp = client.post("/api/auth/login", json={"login": user.login, "password": PASSWORD})
    assert resp.status_code == 200, resp.get_json()
    return resp
