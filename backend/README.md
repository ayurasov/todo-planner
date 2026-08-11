# Todo Planner — Backend (Flask)

Backend спроектирован как реализация под уже существующий frontend
HTTP-слой `src/repositories/http/apiClient.js` (cookie-based сессии,
CSRF-заголовок `X-CSRF-Token`, единый префикс `/api`, без JWT).

## Установка и запуск (development)

```
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
export FLASK_ENV=development
python wsgi.py
```

## Проверка

```
curl http://localhost:5000/api/health
# {"status": "ok"}
```

## Тестирование

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

Все тесты используют in-memory SQLite (`config.TestingConfig`) через фикстуру
`app` в `tests/conftest.py` -- реальная БД не требуется. Покрыто (приоритет
на permissions/auth/ranking -- без гонки за 100%):

- `tests/test_role_matrix.py` (Промпт 18) — полная матрица ролей: global admin,
  list owner/editor/viewer/assignee, пользователь без доступа — для view list /
  create task / edit task (свою/чужую) / delete task / manage members / delete
  list. Зеркалирует `src/services/PermissionService.js` на frontend.
- `tests/test_auth.py` (Промпт 20) — login (успех/неверный пароль/деактивированный
  аккаунт/невалидный payload), logout, `/me`, глобальный login guard,
  `/csrf-token` и CSRF-защита mutating-запросов (отдельная фикстура `csrf_client`
  с включённым `WTF_CSRF_ENABLED`, в остальных тестах CSRF отключён ради простоты).
- `tests/test_crud_dto.py` (Промпт 20) — CRUD для tasks/lists с проверкой, что
  response-DTO приходит в camelCase (`listId`, `dueDate`, `ownerIds`, ...), как
  ожидает `src/repositories/http/apiClient.js`, а не в snake_case ORM-полей.

Frontend-тесты (`vitest`) запускаются отдельно из корня проекта — см. корневой
`README.md`.

### Линтинг

```bash
ruff check .  # минимальный конфиг в backend/ruff.toml (E/F/W, без E501/E741)
```

### CI

На push/PR по путям `backend/**` GitHub Actions запускает `ruff check .` и
`pytest` (workflow `.github/workflows/backend-ci.yml`) — см. раздел «CI/CD»
в корневом `README.md`, включая инструкцию по включению branch protection.

## Структура

- `config.py` — профили `development` / `testing` / `production`.
- `app/extensions.py` — единые инстансы `db` (Flask-SQLAlchemy), `sess`
  (Flask-Session), `cors` (Flask-CORS), `csrf` (Flask-WTF CSRFProtect).
- `app/<module>/__init__.py` + `routes.py` — по одному blueprint на ресурс:
  `health`, `auth`, `users`, `lists`, `tasks`, `meetings`, `recurrence`,
