# Todo Planner — Backend (Flask, каркас)

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

## Структура

- `config.py` — профили `development` / `testing` / `production`.
- `app/extensions.py` — единые инстансы `db` (Flask-SQLAlchemy), `sess`
  (Flask-Session), `cors` (Flask-CORS), `csrf` (Flask-WTF CSRFProtect).
- `app/<module>/__init__.py` + `routes.py` — по одному blueprint на ресурс:
  `health`, `auth`, `users`, `lists`, `tasks`, `meetings`, `recurrence`,
  `history`, `notifications`, `saved_views`, `comments`, `checklists`, `notes`.
- Все роуты, кроме `GET /api/health`, — заглушки `501 Not Implemented`.
  Бизнес-логика (репозитории, сервисы поверх ORM/domain/DTO) сюда сознательно
  не включена — это следующий шаг.
- `wsgi.py` — entrypoint для `gunicorn wsgi:app`.

## Соответствие фронтенду

- `credentials: 'include'` в apiClient.js -> `SESSION_COOKIE_*` в config.py
  + `Flask-Session` (server-side, не JWT).
- Заголовок `X-CSRF-Token` в apiClient.js -> `WTF_CSRF_HEADERS` в config.py.
- `BASE_URL = '/api'` в apiClient.js -> все blueprints зарегистрированы
  с префиксом `/api/...`.
- CORS настроен только на origin dev-сервера фронтенда (`http://localhost:5173`
  по умолчанию, см. `FRONTEND_ORIGIN` в `.env.example`).

## ORM / domain / DTO слои (Промпт 10)

Добавлен слой преобразования данных, не подключённый к routes:

- `app/models/` — SQLAlchemy ORM-модели, 1:1 с таблицами `backend/migrations/*.up.sql`.
- `app/domain/entities.py` — dataclass-сущности, независимые от ORM/Flask/Pydantic;
  аналог `src/domain/entities/factories.js` на фронтенде, но в snake_case (Python-конвенция).
- `app/dto/schemas.py` — Pydantic DTO для request/response; поля в camelCase
  (`alias=...`), чтобы совпадать с тем, что уже ожидает/отдаёт
  `src/repositories/http/apiClient.js` (`globalRole`, `isActive`, `meetingId`,
  `completedAt`, `createdAt`, вложенные `checklist`/`comments`/`history` и т.д.).
- `app/mappers/converters.py` — явные функции `orm_to_domain.*`, `domain_to_dto.*`,
  `dto_to_domain.*` без побочных эффектов и без query к БД.

Слои изолированы: `app/models` ничего не знает о domain/dto, `app/domain` не
импортирует SQLAlchemy/Pydantic, `app/dto` не импортирует SQLAlchemy. Это
готовит почву для будущих `services`, которые будут работать только с
domain-объектами — и для `http`-репозитория на фронтенде, который получит
те же camelCase-поля, что уже возвращает `mock`-репозиторий
(`src/repositories/mock/*`), обеспечивая dual-mode без изменений в Pinia store.

### Пример потока 1: задача (Task)

```python
from app.models import TaskORM
from app.mappers import orm_to_domain, domain_to_dto

task_orm = TaskORM.query.get(task_id)          # persistence (SQLAlchemy)
task = orm_to_domain.task(task_orm)             # -> Task (dataclass, snake_case)
dto = domain_to_dto.task(task)                  # -> TaskResponseDTO (camelCase)
return jsonify(dto.model_dump(by_alias=True))
# {"id": "...", "listId": "...", "assigneeId": "...", "completedAt": null, ...}
```

### Пример потока 2: пользователь (User) при логине

```python
from app.models import UserORM
from app.mappers import orm_to_domain, domain_to_dto

user_orm = UserORM.query.filter_by(login=login).first()
user = orm_to_domain.user(user_orm)             # -> User (global_role, is_active)
dto = domain_to_dto.user(user)                  # -> UserResponseDTO
return jsonify(dto.model_dump(by_alias=True))
# {"id": "...", "globalRole": "admin", "isActive": true, ...}
```

### Пример потока 3: создание задачи (request -> domain)

```python
from app.dto import TaskCreateDTO
from app.mappers import dto_to_domain

payload = TaskCreateDTO.model_validate(request.get_json())  # camelCase JSON от фронта
task = dto_to_domain.task_from_create(payload)               # -> Task (id ещё не назначен)
# далее (в будущем шаге services) task.id генерируется и строка сохраняется в TaskORM
```

Routes/services в этом шаге не реализованы — эндпоинты продолжают
возвращать `501 Not Implemented` (см. `app/tasks/routes.py` и другие).

## Аутентификация (Промпт 11)

Реализована cookie-session аутентификация, совместимая с
`src/repositories/http/apiClient.js`:

- `POST /api/auth/login` принимает `{ "login": "...", "password": "..." }`,
  проверяет `password_hash` через `werkzeug.security.check_password_hash`,
  отклоняет `is_active = false`, создаёт server-side session и возвращает
  `{"user": ...}` без `password_hash`.
- `POST /api/auth/logout` очищает сессию.
- `GET /api/auth/me` возвращает текущего пользователя по `session["user_id"]`,
  иначе отдаёт стабильный JSON `{"error": "auth_required", "message": "Требуется авторизация"}`
  со статусом `401`.
- `GET /api/auth/csrf-token` возвращает `{"csrfToken": "..."}` через
  `flask_wtf.csrf.generate_csrf()`.
- Глобальный guard (`app/auth/security.py`) требует логин для всех route'ов,
  кроме `/api/health`, `/api/auth/login` и `/api/auth/csrf-token`.

### Bootstrap initial users

При первом запуске приложение:

1. вызывает `db.create_all()` для каркаса;
2. если таблица `users` пуста, создаёт пользователей `admin` и `user`;
3. генерирует случайные временные пароли, сохраняет **только hash**;
4. выводит открытые пароли **один раз** в консоль.

Пример консольного вывода при самом первом запуске:

```text
============================================================
Todo Planner: созданы начальные пользователи (пароли показываются только сейчас):
  login=admin  password=...
  login=user   password=...
Сохраните эти пароли — повторно они не выводятся и не хранятся в открытом виде.
============================================================
```

### Примеры curl

Получить CSRF token и сохранить cookie jar:

```bash
curl -c cookies.txt http://localhost:5000/api/auth/csrf-token
# {"csrfToken":"..."}
```

Логин с cookie + CSRF header:

```bash
CSRF=$(curl -s -c cookies.txt http://localhost:5000/api/auth/csrf-token | python -c 'import sys, json; print(json.load(sys.stdin)["csrfToken"])')

curl -i \
  -b cookies.txt -c cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $CSRF" \
  -X POST http://localhost:5000/api/auth/login \
  -d '{"login":"admin","password":"<password-from-console>"}'
```

Проверить текущего пользователя:

```bash
curl -b cookies.txt http://localhost:5000/api/auth/me
```

Выйти из сессии:

```bash
curl -i \
  -b cookies.txt -c cookies.txt \
  -H "X-CSRF-Token: $CSRF" \
  -X POST http://localhost:5000/api/auth/logout
```

### Примеры HTTPie

Получить CSRF token:

```bash
http --session=todo GET :5000/api/auth/csrf-token
```

Логин:

```bash
http --session=todo POST :5000/api/auth/login \
  X-CSRF-Token:<csrf-token> \
  login=admin password=<password-from-console>
```

Текущий пользователь:

```bash
http --session=todo GET :5000/api/auth/me
```

Logout:

```bash
http --session=todo POST :5000/api/auth/logout X-CSRF-Token:<csrf-token>
```

## PermissionService mirror (Промпт 12)

Backend теперь содержит `app/services/permission_service.py` — зеркальное
продолжение frontend `src/services/PermissionService.js`. Идея та же:
frontend-проверки остаются UX-слоем, но реальным источником истины для
авторизации становится backend.

### Mapping правил

| Frontend PermissionService rule | Backend implementation |
| --- | --- |
| `_isGlobalAdmin(userId)` -> `user.globalRole === 'admin'` даёт полный bypass | `PermissionService.is_global_admin(user_id)` проверяет `UserORM.global_role == 'admin'` и используется в начале всех проверок |
| `getRole(listId, userId)` читает роль пользователя в списке | `PermissionService.get_role(list_id, user_id)` читает `ListMembershipORM.role` |
| `canViewList` разрешает доступ, если у пользователя есть любая list-role | `can_view_list` возвращает `True`, если есть membership, либо если пользователь global admin |
| `canCreateTask` разрешает только `owner/editor` | `can_create_task` использует тот же набор ролей `owner/editor` |
| `canEditTask` для задач в списке: `owner/editor`, либо `assignee` только своей задачи | `can_edit_task(task, user_id)` воспроизводит ровно это правило |
| `canEditTask` для задач без списка: только `createdBy` или `assigneeId` | `can_edit_task` для `task.list_id is None` использует тот же fallback |
| `canAssign` разрешает `owner/editor` | `can_assign` использует тот же набор ролей |
| `canManageMembers` разрешает только `owner` | `can_manage_members` использует только роль `owner` |
| `canDeleteList` разрешает только `owner` | `can_delete_list` использует только роль `owner` |
| `canDeleteTask`: global admin, либо создатель, либо `owner/editor` списка | `can_delete_task(task, user_id)` воспроизводит то же поведение |
| `getAccessibleListIds(userId)` возвращает membership-based набор list ids | `get_accessible_list_ids(user_id)` возвращает list ids из `ListMembershipORM`; для global admin — все известные list ids |
| `isTaskVisible(task, { role, userId, isGlobalAdmin })` скрывает от `assignee` чужие задачи, если он не watcher | `is_task_visible(task, role=..., user_id=..., is_global_admin=...)` реализует то же правило |

### Route guards

Добавлены helper-декораторы:

```python
from app.services.permission_service import require_list_permission, require_task_permission

@require_list_permission("can_manage_members")
def add_list_member(list_id):
    ...

@require_task_permission("can_edit_task")
def update_task(task_id):
    ...
```

На mutating-endpoints эти guard'ы возвращают стабильный JSON 403:

```json
{ "error": "permission_denied", "message": "Недостаточно прав ..." }
```

Именно такой ответ backend должен отдавать дальше, чтобы frontend мог
превращать его в `PermissionDeniedError` и корректно откатывать optimistic UI.

### Фильтрация GET-ответов

При реализации реальных `GET /api/lists`, `GET /api/tasks` и других read-endpoints
следующий шаг должен использовать этот же сервис:

- списки — фильтровать через `permission_service.get_accessible_list_ids(user_id)`;
- задачи — для каждой задачи вычислять роль пользователя в её списке и затем
  пропускать через `permission_service.is_task_visible(...)`;
- задачи без списка (`list_id = null`) не должны утекать чужому пользователю,
  если отдельно не будет введено правило для приватных задач-сирот.
