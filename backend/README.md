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
