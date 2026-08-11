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

## Структура

- `config.py` — профили `development` / `testing` / `production`.
- `app/extensions.py` — единые инстансы `db` (Flask-SQLAlchemy), `sess`
  (Flask-Session), `cors` (Flask-CORS), `csrf` (Flask-WTF CSRFProtect).
- `app/<module>/__init__.py` + `routes.py` — по одному blueprint на ресурс:
  `health`, `auth`, `users`, `lists`, `tasks`, `meetings`, `recurrence`,
  `history`, `notifications`, `saved_views`, `comments`, `checklists`, `notes`.
- `app/repositories/` — слой доступа к данным (SQLAlchemy-запросы), возвращает
  domain-объекты через `app.mappers.orm_to_domain`. Реализованы
  `UserRepository`, `ListRepository`, `TaskRepository` +
  `ChecklistItemRepository`/`NoteRepository`/`CommentRepository`,
  `MeetingRepository`, `RecurrenceRepository`, `NotificationRepository`,
  `SavedViewRepository`. Из crud-ресурсов заглушкой `501 Not Implemented`
  остаются только вложения (`attachments`).
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

Слой преобразования данных:

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
импортирует SQLAlchemy/Pydantic, `app/dto` не импортирует SQLAlchemy.

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

### Примеры curl (auth)

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

## PermissionService mirror (Промпт 12)

`app/services/permission_service.py` — зеркальное продолжение frontend
`src/services/PermissionService.js`. Frontend-проверки остаются UX-слоем,
реальным источником истины для авторизации является backend.

### Mapping правил

| Frontend PermissionService rule | Backend implementation |
| --- | --- |
| `_isGlobalAdmin(userId)` -> `user.globalRole === 'admin'` даёт полный bypass | `PermissionService.is_global_admin(user_id)` проверяет `UserORM.global_role == 'admin'` и используется в начале всех проверок |
| `getRole(listId, userId)` читает роль пользователя в списке | `PermissionService.get_role(list_id, user_id)` читает `ListMembershipORM.role` |
| `canViewList` разрешает доступ, если у пользователя есть любая list-role | `can_view_list` возвращает `True`, если есть membership, либо если пользователь global admin |
| `canCreateTask` разрешает только `owner/editor` | `can_create_task` использует тот же набор ролей `owner/editor`; также используется route-ом `PATCH /lists/:id` как правило "кто может редактировать список" |
| `canEditTask` для задач в списке: `owner/editor`, либо `assignee` только своей задачи | `can_edit_task(task, user_id)` воспроизводит ровно это правило |
| `canEditTask` для задач без списка: только `createdBy` или `assigneeId` | `can_edit_task` для `task.list_id is None` использует тот же fallback |
| `canAssign` разрешает `owner/editor` | `can_assign` использует тот же набор ролей |
| `canManageMembers` разрешает только `owner` | `can_manage_members` использует только роль `owner` |
| `canDeleteList` разрешает только `owner` | `can_delete_list` использует только роль `owner` |
| `canDeleteTask`: global admin, либо создатель, либо `owner/editor` списка | `can_delete_task(task, user_id)` воспроизводит то же поведение |
| `getAccessibleListIds(userId)` возвращает membership-based набор list ids | `get_accessible_list_ids(user_id)` возвращает list ids из `ListMembershipORM`; для global admin — все известные list ids |
| `isTaskVisible(task, { role, userId, isGlobalAdmin })` скрывает от `assignee` чужие задачи, если он не watcher | `is_task_visible(task, role=..., user_id=..., is_global_admin=...)` реализует то же правило |

### Route guards

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

## Users / Lists — реализованная бизнес-логика (Промпт 15)

`app/repositories/user_repository.py` и `app/repositories/list_repository.py` —
чистый слой доступа к данным (SQLAlchemy → domain через `app.mappers.orm_to_domain`),
подключённый к route'ам `app/users/routes.py` и `app/lists/routes.py`.

### Users

| Метод | Путь | Права | Описание |
| --- | --- | --- | --- |
| GET | `/api/users` | любой авторизованный | активные пользователи, без `password_hash` |
| GET | `/api/users/:id` | любой авторизованный | один пользователь |
| PATCH | `/api/users/:id` | только `global_role == admin` | `{ globalRole? , isActive? }` — ровно те поля, что шлёт `UsersView.vue` через `usersStore.updateUser` |

Не-admin получает `403 {"error": "permission_denied", ...}`. Неизвестные поля
в PATCH-теле или недопустимое значение `globalRole`/`isActive` — `400
{"error": "validation_error", "details": [...]}`.

### Lists

| Метод | Путь | Права (`permission_service`) | Описание |
| --- | --- | --- | --- |
| GET | `/api/lists` | видны только доступные (`get_accessible_list_ids`); все — для global admin | |
| POST | `/api/lists` | любой авторизованный | создатель автоматически становится `owner` через membership |
| GET | `/api/lists/:id` | `can_view_list` | |
| PATCH | `/api/lists/:id` | `can_create_task` (правило "owner/editor списка", то же, что и для создания задач) | частичное обновление: title/description/color/isShared/defaultView/settings/archived/order |
| DELETE | `/api/lists/:id` | `can_delete_list` (только `owner`) | `ON DELETE CASCADE` удаляет memberships/tasks в БД |
| GET | `/api/lists/:id/memberships` | `can_view_list` | |
| POST | `/api/lists/:id/memberships` | `can_manage_members` (только `owner`) | `{ userId, role }`, `role ∈ {owner, editor, assignee, viewer}`; повторный вызов для существующего userId обновляет роль (совместимо с `HttpListRepository.updateMemberRole`, который вызывает тот же `POST`) |
| DELETE | `/api/lists/:id/memberships/:userId` | `can_manage_members` | |

Ответы всех ресурсов — через существующие DTO (`app.dto.schemas`), camelCase,
поля 1:1 с `src/repositories/mock/MockListRepository.js` /
`MockUserRepository.js` (эталон, которым руководствовался mock-репозиторий
на фронтенде).

### Примеры curl (users/lists)

```bash
# список пользователей
curl -b cookies.txt http://localhost:5000/api/users

# admin меняет роль другого пользователя
curl -i -b cookies.txt -c cookies.txt -H "X-CSRF-Token: $CSRF" -H "Content-Type: application/json" \
  -X PATCH http://localhost:5000/api/users/<user-id> -d '{"globalRole": "admin"}'

# создать список (создатель = owner)
curl -i -b cookies.txt -c cookies.txt -H "X-CSRF-Token: $CSRF" -H "Content-Type: application/json" \
  -X POST http://localhost:5000/api/lists -d '{"title": "Работа"}'

# добавить участника со списка со ролью viewer
curl -i -b cookies.txt -c cookies.txt -H "X-CSRF-Token: $CSRF" -H "Content-Type: application/json" \
  -X POST http://localhost:5000/api/lists/<list-id>/memberships -d '{"userId": "<user-id>", "role": "viewer"}'

# попытка viewer-а удалить список -> 403 permission_denied
curl -i -b cookies.txt -c cookies.txt -H "X-CSRF-Token: $CSRF" \
  -X DELETE http://localhost:5000/api/lists/<list-id>
```

## Meetings / Recurrence / Notifications / SavedViews (Промпт 17)

### Client/server split: meetings/recurrence/notifications

Некоторые вычисления, которые в mock-режиме делал фронтенд (`src/services`,
`src/stores`), теперь либо перенесены на backend как единственный источник
правды, либо остаются "как есть" на фронте, если они опираются на уже
существующие server-side эндпоинты и не создают риска рассинхронизации между
клиентами:

- **unfinishedCount встреч** — перенесено на backend.
  `MeetingRepository.unfinished_total_count` считает количество задач серии
  (`tasks.meeting_id == meetings.id`) со статусом, отличным от `done`/`cancelled`,
  и это поле возвращается в `MeetingResponseDTO.unfinishedCount` при любом
  чтении встречи (`GET /meetings`, `GET /meetings/:id`, create/update). Это
  аналог `MeetingDetailView.vue.unfinishedTotalCount`, но posчитанный один раз
  на сервере, а не пересчитываемый каждым клиентом из полного списка задач.
- **Генерация следующего инстанса completion_based-серии** — перенесено на
  backend. `RecurrenceRepository.on_task_completed` (порт
  `RecurrenceService.js.onTaskCompleted` + `computeNextOccurrence`) вызывается
  из `app/tasks/routes.py.update_task` в момент перехода `status -> done`,
  а не только на фронте (`tasksStore` там же вызывал `recurrenceService`).
  `fixed_schedule`-шаблоны не генерируются здесь — их инстансы создаются
  заранее background job'ом (вне скопа этого шага, см. Roadmap).
- **unfinishedGroupsByOccurrence на MeetingDetailView.vue** — оставлено на
  фронтенде как есть. Это чисто UI-группировка уже полученного списка задач
  серии (`GET /tasks?listId=...` + фильтр `meetingId`/`occurrenceId` на
  клиенте), не требует отдельного backend-агрегата и не создаёт рисков
  рассинхронизации, так как исходные данные (задачи) уже приходят с сервера.
- **due_soon / overdue уведомления** — временно остаются как создание через
  `POST /notifications` с фронтенда (аналог того, как это делал
  `tasksStore`/`NotificationService.js` в mock-режиме): клиент сам сравнивает
  `dueDate` задач с текущим временем и создаёт уведомление через этот
  эндпоинт. Полноценный перенос на серверный scheduler/background job,
  который сканирует все `due_date` независимо от того, открыт ли у кого-то
  клиент, — задача Промпта 19 (см. Roadmap), в этом шаге не реализована.

### Meetings

| Метод | Путь | Описание |
| --- | --- | --- |
| GET | `/api/meetings` | все встречи, каждая с `unfinishedCount` |
| POST | `/api/meetings` | создание встречи + участников |
| GET | `/api/meetings/:id` | одна встреча |
| PATCH | `/api/meetings/:id` | частичное обновление; `occurrences` в теле полностью заменяет список подстреч (порт `meetingsStore.ensureOccurrences`/`updateOccurrence`) |
| DELETE | `/api/meetings/:id` | удаление; связанные задачи получают `meetingId=null` |
| GET | `/api/meetings/:id/occurrences` | список подстреч регулярной серии |

### Recurrence templates

| Метод | Путь | Описание |
| --- | --- | --- |
| GET | `/api/recurrence?listId=` | список шаблонов, опционально по списку |
| POST | `/api/recurrence` | создание шаблона |
| GET | `/api/recurrence/:id` | один шаблон |
| PATCH | `/api/recurrence/:id` | частичное обновление |
| DELETE | `/api/recurrence/:id` | удаление |

### Notifications

| Метод | Путь | Описание |
| --- | --- | --- |
| GET | `/api/notifications?userId=` | по умолчанию — уведомления текущего пользователя |
| POST | `/api/notifications` | создание уведомления (временное решение, см. выше) |
| PATCH | `/api/notifications/:id` | `{ read: true/false }` |
| DELETE | `/api/notifications/:id` | удаление |
| POST | `/api/notifications/mark-all-read` | массовая отметка прочитанным для текущего пользователя |

### Saved views

Личный ресурс — всегда привязан к `user_id` текущего пользователя;
PATCH/DELETE чужого вида возвращают `403 permission_denied`.

| Метод | Путь | Описание |
| --- | --- | --- |
| GET | `/api/saved-views?userId=` | по умолчанию — виды текущего пользователя |
| POST | `/api/saved-views` | создание |
| PATCH | `/api/saved-views/:id` | частичное обновление |
| DELETE | `/api/saved-views/:id` | удаление |

## Оставшиеся заглушки 501

Остаются заглушками только вложения задач: `GET/POST /tasks/:id/attachments`
(файловое хранилище — отдельная задача, см. корневой README.md, раздел
"Roadmap").

## Миграции и БД

Production-режим ориентирован на **PostgreSQL**; локально и в тестах остаётся **SQLite** через профили из `config.py`.

### Выбор БД по окружению

- `FLASK_ENV=development` — по умолчанию `sqlite:///backend/todo_planner.db`, если не задан `DATABASE_URL`.
- `FLASK_ENV=testing` — всегда `sqlite:///:memory:` для быстрых pytest/integration tests.
- `FLASK_ENV=production` — рекомендуется задавать `DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname`.

`DATABASE_URL` — основной production-источник; `SQLALCHEMY_DATABASE_URI` остаётся совместимым override для нестандартных сценариев.

### Alembic: базовые команды

Первичная инициализация/обновление схемы:

```bash
cd backend
source .venv/bin/activate
export FLASK_ENV=development
alembic upgrade head
```

Откат последней миграции:

```bash
alembic downgrade -1
```

Откат до конкретной ревизии:

```bash
alembic history
alembic downgrade <revision_id>
```

Создание новой миграции после изменения ORM-моделей:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

### Деплой

Backend больше **не** полагается на `db.create_all()` вне тестового профиля. Порядок шагов при деплое:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export FLASK_ENV=production
export DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname
alembic upgrade head
python wsgi.py
```

Если приложение стартует на пустой БД без выполненных миграций, оно выведет warning в лог о необходимости `alembic upgrade head`; автосоздание production-схемы отключено намеренно.

### Connection pooling

Для production включён умеренный pooling SQLAlchemy без over-engineering:

- `pool_size=5`
- `max_overflow=5`
- `pool_pre_ping=True`
- `pool_recycle=1800`

Значения подходят для небольшой команды и переопределяются через `DB_POOL_SIZE` / `DB_MAX_OVERFLOW`.
