# Todo Planner — v2.0.0

[![Frontend CI](https://github.com/ayurasov/todo-planner/actions/workflows/frontend-ci.yml/badge.svg)](https://github.com/ayurasov/todo-planner/actions/workflows/frontend-ci.yml)
[![Backend CI](https://github.com/ayurasov/todo-planner/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/ayurasov/todo-planner/actions/workflows/backend-ci.yml)
[![E2E smoke](https://github.com/ayurasov/todo-planner/actions/workflows/e2e.yml/badge.svg)](https://github.com/ayurasov/todo-planner/actions/workflows/e2e.yml)

Веб-планировщик задач на Vue 3 + Vite + Pinia + Vue Router + ECharts.
Реализован по утверждённой архитектуре (repository/adapter pattern, готовый к переходу на Flask+SQLite v2 без переписывания UI).

## Deployment

Основной способ запуска на сервере — через Docker Compose:

```bash
cp .env.example .env
# обязательно задайте SECRET_KEY, POSTGRES_PASSWORD, DATABASE_URL, FRONTEND_ORIGIN
# SECRET_KEY: python -c "import secrets; print(secrets.token_hex(32))"

docker compose up -d --build
```

Что поднимется:

- `db` — `postgres:16-alpine` с volume `db_data`.
- `backend` — Flask/Gunicorn контейнер из `backend/Dockerfile`; перед стартом приложения
  entrypoint ждёт доступность Postgres и выполняет `alembic upgrade head`.
- `frontend` — статическая сборка Vite в nginx; nginx отдаёт SPA и проксирует `/api/*`
  в backend (`http://backend:5000/api/*`), поэтому приложение работает в same-origin режиме.
- `backup` — sidecar на `postgres:16-alpine`, который делает ежедневный `pg_dump -Fc`
  в volume `db_backups` и удаляет файлы старше `BACKUP_RETENTION_DAYS`.

После запуска:

- фронтенд доступен на `http://localhost` (или на IP/домене сервера, если порт 80 открыт наружу);
- backend healthcheck — `http://localhost/api/health` через nginx reverse-proxy;
- прямой backend внутри compose-сети слушает `http://backend:5000`.

### Что внутри контейнеров

- `backend/Dockerfile` — multi-stage образ на `python:3.12-slim`, production WSGI-сервер `gunicorn`,
  healthcheck на `/api/health`.
- `Dockerfile` (корень проекта) — multi-stage сборка фронтенда: `npm ci` + `npm run build`,
  финальный runtime-образ — `nginx:alpine`.
- `docker-compose.yml` — сервисы `db`, `backend`, `frontend`, `backup` с healthchecks и порядком старта:
  `backend` зависит от healthy `db`, `frontend` зависит от healthy `backend`, `backup` ждёт healthy `db`.

### Продовые переменные

См. корневой `.env.example`:

- `DATABASE_URL` — строка подключения к Postgres для backend;
- `SECRET_KEY` — обязательный секрет Flask-сессий/CSRF; без него backend **не стартует**;
- `FRONTEND_ORIGIN` — публичный origin фронтенда (например, `https://todo.example.com`);
- `SESSION_COOKIE_SAMESITE` — политика cookie (`Lax` по умолчанию; `None` только вместе с HTTPS);
- `RATELIMIT_STORAGE_URI` и `LOGIN_RATE_LIMIT` — настройки rate limiting для `POST /api/auth/login`;
- `BACKUP_RETENTION_DAYS` — сколько дней хранить `pg_dump`-бэкапы;
- `VITE_API_MODE=http` — фронтенд собирается в HTTP-режиме;
- `VITE_API_BASE_URL=/api` — фронтенд обращается к backend через same-origin nginx proxy.

### HTTPS / reverse-proxy

Для реального сервера приложение должно публиковаться **не напрямую через `frontend:80`**, а через reverse-proxy с TLS.
В проекте выбран **Caddy** как наиболее простой вариант: он сам выпускает и продлевает сертификаты Let's Encrypt.

Минимальная схема:

1. Оставить `frontend` как внутренний nginx на `:80` внутри compose-сети.
2. Убрать внешний `ports: ["80:80"]` у `frontend` в production-сборке.
3. Поставить перед ним Caddy с `ports: ["80:80", "443:443"]`.
4. Настроить `reverse_proxy frontend:80` и домен в `Caddyfile`.

В репозитории уже добавлен `Caddyfile.example`:

```caddy
# замените todo.example.com на ваш домен

todo.example.com {
    reverse_proxy frontend:80

    encode gzip

    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "strict-origin-when-cross-origin"
    }
}
```

Пример сервиса Caddy для `docker-compose.yml`:

```yaml
  caddy:
    image: caddy:2-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      frontend:
        condition: service_healthy
```

Важно:

- `FRONTEND_ORIGIN` в `.env` должен совпадать с публичным `https://...` доменом.
- В production backend ставит `SESSION_COOKIE_SECURE=True`, `SESSION_COOKIE_HTTPONLY=True`
  и требует реальный `SECRET_KEY` из env; при использовании `SESSION_COOKIE_SAMESITE=None`
  HTTPS обязателен.
- `ProxyFix` в backend уже включён для production, поэтому `X-Forwarded-For` / `X-Forwarded-Proto`
  от nginx/Caddy корректно учитываются для логов, CSRF/secure-cookies и rate limiting.

### Backup / ротация

В `docker-compose.yml` добавлен сервис `backup`, который раз в день в `03:00 UTC` выполняет:

```bash
pg_dump -Fc -f /backups/todo_planner_YYYYmmddTHHMMSSZ.dump
find /backups -name '*.dump' -mtime +$BACKUP_RETENTION_DAYS -delete
```

Это минимальный, но рабочий baseline для эксплуатации:

- backup-файлы лежат в Docker volume `db_backups`;
- retention регулируется переменной `BACKUP_RETENTION_DAYS` (по умолчанию 14);
- формат `-Fc` подходит для точечного восстановления через `pg_restore`.

Примеры ручных команд:

```bash
# список файлов

docker volume inspect todo-planner_db_backups

# разовый manual backup

docker compose exec backup sh -c 'FILE=/backups/manual_$(date -u +%Y%m%dT%H%M%SZ).dump && pg_dump -Fc -f "$FILE" && echo $FILE'

# восстановление в пустую БД (пример)

docker compose exec -T db dropdb -U "$POSTGRES_USER" "$POSTGRES_DB"
docker compose exec -T db createdb -U "$POSTGRES_USER" "$POSTGRES_DB"
docker compose exec -T backup sh -c 'pg_restore -d "$PGDATABASE" /backups/<backup-file>.dump'
```

Для SQLite (development/testing) достаточно ротации snapshot-копий файла БД по cron на хосте;
для production-окружения основной сценарий здесь — Postgres + `pg_dump`.

### Логирование и базовые security-controls

Backend для production теперь включает:

- `SESSION_COOKIE_SECURE=True`, `SESSION_COOKIE_HTTPONLY=True`, настраиваемый `SESSION_COOKIE_SAMESITE`;
- fail-fast старт при пустом/placeholder `SECRET_KEY`;
- rate limiting на `POST /api/auth/login` (`Flask-Limiter`) против brute-force;
- `POST /api/auth/change-password` для авторизованного пользователя;
- structured JSON logging через `app.logger`/stdout вместо `print()` для ошибок и operational log shipping.

### Обновление после новой версии

```bash
docker compose up -d --build
```

Compose пересоберёт frontend/backend образы, backend снова применит `alembic upgrade head`,
после чего gunicorn поднимет обновлённое приложение.

## Запуск

```bash
npm install
npm run dev
```

Откройте http://localhost:5173

## Сборка production

```bash
npm run build
npm run preview
```

## Структура

- `src/domain` — сущности, enum'ы, чистый алгоритм ranking score (без Vue/зависимостей).
- `src/repositories` — контракты (интерфейсы) + mock- и http-реализации.
  Единая точка внедрения — `src/repositories/index.js`, переключается переменной `VITE_API_MODE`.
- `src/integrations/calendar` — абстракция CalendarProvider + mock-реализация (Exchange-подобная, заглушка).
- `src/services` — PermissionService, HistoryService, RecurrenceService.
- `src/stores` — Pinia store'ы (users, lists, tasks, view, history, recurrence, calendar, auth, notifications).
- `src/components` — UI-компоненты (задачи, чарты, общие элементы).
- `src/views` — экраны: My Tasks, Team Tasks, List View, Recurring, History, Settings, Login.

## Тестирование

Unit-тесты покрывают самую критичную бизнес-логику frontend — ranking/bubble-
сортировку задач и матрицу прав доступа (зеркальную backend-версии), а также
сервис рекуррентных задач. Vue-компоненты не рендерятся -- тесты проверяют
только чистую логику (`src/domain`, `src/services`).

```bash
npm install
npm run test        # разовый прогон (vitest run)
npm run test:watch  # watch-режим для локальной разработки
```

Что покрыто:
- `src/domain/ranking/rankingScore.js` — расчёт ranking score, сортировка, `explainVisibility`.
- `src/domain/ranking/bubbleSort.js` — разбиение на bubble-тиры и сортировка внутри блоков.
- `src/services/PermissionService.js` — та же ролевая матрица (admin/owner/editor/viewer/assignee),
  что и в `backend/tests/test_role_matrix.py` — гарантирует зеркальность правил между frontend и backend.
- `src/services/RecurrenceService.js` — расчёт следующей даты повторения (`computeNextOccurrence`)
  и генерация следующего инстанса задачи.

Backend-тесты (`pytest`) запускаются отдельно — см. `backend/README.md`.

### Линтинг

```bash
npm run lint  # eslint . — минимальный flat-конфиг в eslint.config.js
```

## CI/CD (Промпт 21)

На каждый push в `main` и на каждый pull request запускаются два независимых
GitHub Actions workflow (`.github/workflows/`):

- **`frontend-ci.yml`** — триггерится по путям `src/**`, `package.json` и
  конфигам сборки/тестов. Шаги: `npm ci` → `npm run lint` (eslint) →
  `npm run test` (vitest из Промпта 20) → `npm run build`. Падает при любой
  ошибке линтинга, упавшем тесте или неудачной сборке.
- **`backend-ci.yml`** — триггерится по путям `backend/**`. Шаги:
  `pip install -r requirements.txt -r requirements-dev.txt` →
  `ruff check .` (минимальный конфиг в `backend/ruff.toml`) → `pytest`
  (тесты из Промпта 20/23). Падает при любой ошибке линтинга или упавшем тесте.

Статус обоих workflow отражён бейджами в начале этого файла.

### Как включить branch protection (блокировка merge при красном CI)

Сами workflow только запускают проверки и падают при ошибках — чтобы это
реально блокировало merge pull request'ов, нужно один раз включить branch
protection rules в настройках репозитория (workflow этого не делают
автоматически):

1. Откройте **Settings → Branches** в репозитории на GitHub.
2. В разделе **Branch protection rules** нажмите **Add branch protection rule**
   (или **Add rule**).
3. В поле **Branch name pattern** укажите `main`.
4. Включите **Require status checks to pass before merging**.
5. В списке статус-чеков найдите и отметьте `Lint, test & build` (job из
   `frontend-ci.yml`) и `Lint & test` (job из `backend-ci.yml`) — они
   появятся в списке после первого запуска workflow на любом PR.
6. Рекомендуется также включить **Require branches to be up to date before
   merging**, чтобы CI гонял актуальный код перед merge.
7. Сохраните правило (**Create** / **Save changes**).

После этого GitHub заблокирует кнопку **Merge** на любом PR, где хотя бы один
из выбранных статус-чеков не прошёл (красный крестик), пока ошибки не будут
исправлены.

## Данные

В v1 данные — mock, хранятся в `localStorage` (переживают обновление страницы, решение по допущению #3).
Чтобы сбросить к seed-данным — очистите localStorage браузера (ключи с префиксом `todo-planner:v1:`).

## Ranking score / "вываливание вверх" / "исчезание"

См. `src/domain/ranking/rankingScore.js` — прозрачный алгоритм с явным разложением по факторам
(overdue, dueSoon, recency, assignedToMe, pinned, priority). Веса зафиксированы как константы (RANKING_WEIGHTS).

## Dual-mode: mock | http

Приложение может работать в двух режимах, без изменения stores/services/UI:

- `VITE_API_MODE=mock` (по умолчанию) — localStorage/mock-репозитории, всё разрешено, backend не нужен.
- `VITE_API_MODE=http` — HTTP-репозитории через `src/repositories/http/apiClient.js` (cookie-сессии, CSRF, backend — источник истины для permissions, см. `backend/app/services/permission_service.py`).

См. `.env.example` для `VITE_API_MODE`/`VITE_API_BASE_URL`.

### Mapping: repository contract → HTTP endpoints → stores/components

| Repository contract | HTTP endpoints | Stores / компоненты |
| --- | --- | --- |
| `TaskRepository` → `HttpTaskRepository` | `GET/POST /api/tasks`, `GET/PATCH/DELETE /api/tasks/:id` | `tasksStore`, `useTaskPermissions`, `TaskRow`, `TaskDetailPanel`, `ListView`, `MyTasksView`, `TeamTasksView` |
| `ListRepository` → `HttpListRepository` | `GET/POST /api/lists`, `GET/PATCH/DELETE /api/lists/:id`, `GET/POST /api/lists/:id/memberships`, `DELETE /api/lists/:id/memberships/:userId` | `listsStore`, `useListPermissions`, `ListsManagerView` |
| `UserRepository` → `HttpUserRepository` | `GET /api/users`, `GET/PATCH /api/users/:id`, `GET /api/auth/me` | `usersStore`, `UsersView`, router admin-guard |
| `HistoryRepository` → `HttpHistoryRepository` | `GET /api/history?taskId=/listId=/userId=` (append — no-op, backend сам пишет историю при мутациях) | `HistoryService`, `HistoryView` |
| `RecurrenceRepository` → `HttpRecurrenceRepository` | `GET/POST /api/recurrence-templates`, `GET/PATCH/DELETE /api/recurrence-templates/:id` | `RecurrenceService` |
| `SavedViewRepository` → `HttpSavedViewRepository` | `GET/POST /api/saved-views`, `PATCH/DELETE /api/saved-views/:id` | сохранённые виды (если используются в UI) |
| `HttpChecklistRepository` (implicit contract) | `POST /api/tasks/:taskId/checklist-items`, `PATCH/DELETE /api/checklist-items/:id` | `tasksStore.checklistByTask` |
| `HttpNoteRepository` (implicit contract) | `GET /api/tasks/:taskId/notes`, `POST /api/tasks/:taskId/notes`, `PATCH /api/notes/:id` | `tasksStore.notesByTask` |
| `CommentRepository` → `HttpCommentRepository` | `GET/POST /api/tasks/:taskId/comments`, `PATCH/DELETE /api/comments/:id` | `tasksStore.commentsByTask` |
| `NotificationRepository` → `HttpNotificationRepository` | `GET /api/notifications?userId=`, `POST /api/notifications`, `PATCH /api/notifications/:id`, `POST /api/notifications/mark-all-read`, `DELETE /api/notifications/:id` | `notificationsStore` |
| `MeetingRepository` → `HttpMeetingRepository` | `GET/POST /api/meetings`, `GET/PATCH/DELETE /api/meetings/:id` | `MeetingsView`, `MeetingDetailView` |

### Авторизация (только в http-режиме)

`src/main.js` до `app.mount()` вызывает `authStore.bootstrap()`: `GET /api/auth/csrf-token` → `apiClient.setCsrfToken(...)` → `GET /api/auth/me`.
При 401 `authStore.authenticated = false`, `App.vue` не загружает authenticated-данные, а `router` (guard в `src/router/index.js`) перекидывает на `/login` (`LoginView.vue`).
`usersStore.currentUser` в http-режиме всегда приходит из `GET /api/auth/me` (через `HttpUserRepository.getCurrentUser()`), а не из seed-данных.

### Обработка 403/401 в stores

`src/stores/utils/withPermissionHandling.js` — единая готча для mutating actions (`tasksStore._guarded`, `listsStore._guarded`, `usersStore.updateUser`). При `PermissionDeniedError` от backend вызывается `rollback`, если передан, в `notificationsStore.items` кладётся toast, и ошибка ретроуится для UI. При `AuthRequiredError` — редирект на `/login`. В mock-режиме эти ошибки никогда не выбрасываются, поведение mock не меняется.

## Architecture v2 / Runtime modes

Этот раздел описывает **текущую фактическую архитектуру** (не план) на момент завершения перехода v1 → v2:
фронтенд (Vue 3 + Pinia) умеет работать как полностью автономно (mock), так и поверх настоящего backend
(Flask + SQLite + server-side сессии + server-side permissions), не меняя ни код stores, ни компоненты UI —
только переменную окружения.

Фактически реализовано на момент этого раздела:

- Полный набор экранов: My Tasks, Team Tasks, List View, Lists Manager, Meetings + Meeting Detail (с разбором
  резюме встречи в задачи через `MeetingSummaryParser`), History, Analytics, Settings, Users (admin-only), Login.
- Bubble view ("пузырьковая" группировка Не выполнено / Выполнено, `src/domain/ranking/bubbleSort.js`) и Quick
  Filters (`filtersStore.js`) как отдельные, независимые от группировки/сортировки механизмы.
- История изменений задач (`HistoryService` + `HistoryRepository`/`HttpHistoryRepository`).
- Полноценный auth-экран (`LoginView.vue`) и `authStore` с bootstrap-последовательностью csrf → me.
- 11 HTTP-репозиториев (`src/repositories/http/*`), зеркалирующих mock-репозитории 1:1 по контракту.
- Backend-каркас: Flask blueprints на каждый ресурс, ORM/domain/DTO слои с мэппером camelCase ↔ snake_case,
  cookie-session аутентификация (`/api/auth/*`), CSRF-защита, и зеркальный `PermissionService` на Python,
  повторяющий правила фронтенд `PermissionService.js` (см. `backend/README.md`, раздел "PermissionService mirror").

### Режим A — `VITE_API_MODE=mock` (полностью локальный)

Запуск:

```bash
npm install
cp .env.example .env        # VITE_API_MODE=mock (или не создавать .env — mock это default)
npm run dev
```

- Backend не требуется вообще.
- Все данные — в `localStorage` браузера (переживают reload), сид генерируется при первом запуске.
- Permissions проверяются только на клиенте (`PermissionService.js`) — это UX-слой, а не защита; любой,
  кто откроет devtools, может обойти проверку. Приемлемо для локальной разработки/демо без реального backend.

### Режим B — `VITE_API_MODE=http` (Flask + SQLite + session auth + server-side permissions)

Запуск backend:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
export FLASK_ENV=development
python wsgi.py
# слушает http://localhost:5000, при первом запуске печатает в лог
# временные пароли для пользователей admin/user — сохраните их сразу
```

Для ручного/авто-тестирования матрицы ролей (не только admin/user) запустите дополнительно seed-скрипт с
реалистичным набором участников:

```bash
cd backend
source .venv/bin/activate
export FLASK_ENV=development
python seed_demo_data.py
# создаёт demo-admin1/demo-admin2 (global admin), demo-alice/demo-bob/demo-carol
# (обычные пользователи) и списки с разными комбинациями ролей owner/editor/
# viewer/assignee — пароли печатаются в лог один раз. Скрипт идемпотентен,
# повторный запуск не создаёт дублей.
```

Запуск фронтенда (в отдельном терминале):

```bash
cp .env.example .env
# в .env выставить:
#   VITE_API_MODE=http
#   VITE_API_BASE_URL=http://localhost:5000/api
npm install
npm run dev
```

- Открыть http://localhost:5173 — приложение покажет `LoginView`, пока не будет активной сессии.
- Авторизоваться логином/паролем из логов backend (`admin` или `user`, либо `demo-*` после запуска
  `seed_demo_data.py`).
- Сессии — cookie-based (`Flask-Session`, не JWT), CSRF — заголовок `X-CSRF-Token`, полученный через
  `GET /api/auth/csrf-token` (детали см. `backend/README.md`).

### Переключение mock ↔ http

Переключение — это правка **только** `.env` (`VITE_API_MODE=mock` или `http` + `VITE_API_BASE_URL`), без
изменения кода. `src/repositories/index.js` — единственная точка, которая читает эту переменную и подставляет
нужный набор репозиториев; все stores и компоненты обращаются только к экспортам из `src/repositories/index.js`
и не знают, какой режим активен.

## Smoke-checklist (ручная проверка) + автоматизация (Playwright)

Шаги 1-7 ниже теперь **автоматизированы** Playwright E2E-тестами (`e2e/*.spec.js`, Промпт 24) и гоняются
против docker-compose стека (Промпт 22) в CI (`.github/workflows/e2e.yml`). Ручной прогон остаётся нужен
для шагов 8-9 (требуют `seed_demo_data.py` с недетерминированными паролями) и как fallback/дебаг.

Запуск автотестов — см. `e2e/README.md`:

```bash
docker compose up -d --build
docker compose exec backend python seed_e2e_data.py   # детерминированные e2e-admin/e2e-owner/e2e-viewer
npm install && npx playwright install --with-deps chromium
npm run e2e
```

Выполнять ручную версию после любого значимого изменения в auth/permissions/repositories слоях, в режиме
`VITE_API_MODE=http` (если не указано иное). Для шагов 8-9 предварительно запустите `python seed_demo_data.py`
(см. выше) — он создаёт пользователей с ролями Owner/Editor, необходимыми для этих проверок.

1. **Login/logout** — открыть `/`, убедиться в редиректе на `/login`; ввести логин/пароль из логов backend →
   попасть на `/my-tasks`; выполнить logout (кнопка в `AppTopBar`/`SettingsView`) → редирект обратно на `/login`,
   повторный заход на `/my-tasks` без логина снова уводит на `/login`.
2. **Получение CSRF token** — открыть devtools → Network при первой загрузке приложения, убедиться, что
   выполняется `GET /api/auth/csrf-token` до `POST /api/auth/login`, и что последующие мутирующие запросы
   (`POST/PATCH/DELETE`) содержат заголовок `X-CSRF-Token`.
3. **401 → экран логина** — вручную удалить cookie сессии (или дождаться истечения) и обновить страницу /
   выполнить любое действие → приложение должно показать `LoginView`, а не белый экран/необработанную ошибку.
   Отдельно: при **недоступности backend** (сетевая ошибка/5xx, не 401/403) приложение показывает полноэкранный
   экран «Не удаётся связаться с сервером» с кнопкой «Повторить» (`App.vue`/`authStore.networkError`), а не
   белый экран или бесконечный спиннер — покрыто `e2e/network-failure.spec.js` (Промпт 24).
4. **403 → откат optimistic update + toast** — залогиниться пользователем без прав на список/задачу (например,
   `Viewer` в чужом списке), попытаться изменить статус задачи → изменение в UI должно откатиться к исходному
   значению, а в списке уведомлений должен появиться toast «Недостаточно прав».
5. **Viewer не может редактировать задачу ни через UI, ни через API** — в UI кнопки редактирования должны быть
   скрыты/disabled (`useTaskPermissions`); дополнительно проверить прямым `curl -b cookies.txt -X PATCH
   .../api/tasks/:id ...` от имени Viewer — backend должен вернуть `403 {"error": "permission_denied"}`, а не 200.
6. **Admin видит экран пользователей и все списки** — залогиниться как `admin`, открыть `/settings/users`
   (должен открыться, а не редиректить назад), и убедиться, что в `Lists Manager` видны списки, где admin не
   состоит явным участником (bypass через `is_global_admin`).
7. **Переключение mock ↔ http только через `.env`** — поменять `VITE_API_MODE` в `.env`, перезапустить
   `npm run dev` (без правок в `src/`) → приложение должно продолжать работать в новом режиме.
8. **Editor может создавать/редактировать задачи, но не управлять участниками и не удалять список** —
   залогиниться как `demo-bob` (Editor в списке `Demo: Marketing`), убедиться, что кнопки "Создать задачу" и
   редактирование любой задачи списка доступны и проходят успешно; открыть настройки списка/участников — пункт
   управления участниками и кнопка удаления списка должны быть скрыты/disabled в UI, а прямой `curl -X POST
   .../api/lists/:id/memberships` и `curl -X DELETE .../api/lists/:id` от имени Editor — вернуть `403`.
9. **Owner может управлять участниками и удалять список, Viewer/Assignee — нет** — залогиниться как
   `demo-alice` (Owner в `Demo: Marketing`), добавить/удалить участника через `Lists Manager` → должно пройти
   успешно (`201`/`204`); затем залогиниться как `demo-carol` (Viewer в этом же списке) — раздел управления
   участниками должен быть скрыт в UI, а `curl -X POST .../api/lists/:id/memberships` от её имени — вернуть
   `403`. Дополнительно проверить, что Assignee (`demo-carol` в списке `Demo: Engineering`) может редактировать
   только назначенные на неё задачи, но получает `403` при попытке отредактировать чужую задачу того же списка.

## Известные ограничения

Актуализировано по итогам Промптов 15-24 (v2.0.0).

- **Нет real-time sync между несколькими клиентами.** Если два пользователя одновременно открывают одну задачу
  или список, изменения одного не долетают до другого без ручного обновления страницы — WebSocket/SSE слоя нет.
  *(Из Roadmap v1 — до сих пор не реализовано, остаётся в Roadmap ниже.)*
- **Нет background jobs / очереди.** Генерация повторяющихся задач и сканирование due-soon/overdue выполняются
  клиентски (`tasksStore.scanDueNotifications`) при каждой загрузке приложения, а не сервером по расписанию —
  Celery/RQ не подключены. *(Из Roadmap v1 — до сих пор не реализовано, остаётся в Roadmap ниже.)*
- **`MeetingSummaryParser` — не LLM, а regex-эвристика.** Разбор резюме встречи в задачи (`MeetingDetailView`)
  работает по фиксированным шаблонам текста, а не через языковую модель; контракт `SummaryParser` спроектирован
  как заменяемая абстракция, но реальная LLM-интеграция не подключена. *(Из Roadmap v1 — до сих пор не
  реализовано, остаётся в Roadmap ниже.)*
- **Нет отдельного audit log.** Существует только `History` изменений задач (`HistoryService` +
  `HistoryRepository`) — изменения списков, участников, ролей и попыток 403 в неизменяемый журнал не пишутся.
  *(Из Roadmap v1 — до сих пор не реализовано, остаётся в Roadmap ниже.)*
- **E2E-тесты покрывают только базовый smoke.** Playwright (`e2e/*.spec.js`, Промпт 24) автоматизирует шаги
  1-7 smoke-checklist (login/logout, 401, 403+toast, Viewer-ограничения, admin-доступ, dual-mode) и
  silent-failure сценарий, но не шаги 8-9 (Editor/Owner-управление участниками, требуют `seed_demo_data.py` с
  недетерминированными паролями) — они остаются ручными.
- **Возможны повторные полные загрузки после мутаций.** Stores (`tasksStore`, `listsStore` и др.) не полностью
  нормализованы (нет единого entity-cache с автоматической инвалидацией по связям), поэтому отдельные операции
  дозагружают смежные данные (например, `checklistByTask`/`commentsByTask`) отдельными запросами вместо одного
  батч-запроса.
- **Проверка прав асимметрична по режимам.** В mock-режиме permissions проверяются только клиентом
  (`PermissionService.js`) — это чисто UX-слой без реальной защиты. В http-режиме проверяются и клиент (для
  мгновенного UX — скрытие кнопок, disabled-состояния), и сервер (`permission_service.py`, реальный источник
  истины, отдаёт 403 на нарушения).
- **Rate limiting по умолчанию memory-based.** Текущая конфигурация `Flask-Limiter` подходит для single-instance
  deployment; при нескольких backend-репликах или gunicorn worker'ах для строгой общей квоты лучше вынести
  `RATELIMIT_STORAGE_URI` в Redis.
- **Backup-rotation здесь базовая.** Ежедневный `pg_dump` в Docker volume решает baseline-восстановление, но не
  заменяет offsite/backblaze/s3-репликацию, мониторинг успешности backup-job и регулярные restore-drill проверки.

## Roadmap: что дальше после v2

Обновлено по итогам Промптов 15-24 — отмечено, что уже сделано, что остаётся.

- **Webhooks / real-time sync** — ❌ не реализовано. WebSocket или SSE канал для обновления задач/списков у
  всех подключённых клиентов без polling.
- **Background jobs** — ❌ не реализовано. Очередь (Celery/RQ) для генерации повторяющихся задач по расписанию,
  напоминаний due-soon/overdue и других отложенных операций вместо клиентского `scanDueNotifications`.
- **Import summary via LLM** — ❌ не реализовано. Замена regex-эвристики `MeetingSummaryParser` на реальный
  LLM-based парсер резюме встреч в задачи (контракт `SummaryParser` уже спроектирован как заменяемая
  абстракция).
- **Audit logging** — ❌ не реализовано. Отдельный неизменяемый журнал действий (кто/что/когда), шире, чем
  текущая `History` задач, — включая изменения списков, участников, ролей и попытки 403.
- **E2E tests** — ✅ реализовано частично (Промпт 24). Playwright-сценарии (`e2e/*.spec.js`) автоматизируют
  шаги 1-7 smoke-checklist и silent-failure сценарий, гоняются в CI (`.github/workflows/e2e.yml`) против
  docker-compose стека. Осталось: шаги 8-9 (Editor/Owner-управление участниками) и расширение покрытия
  (создание/удаление задач, чек-листы, комментарии).
- **Role-matrix integration tests** — ✅ реализовано на backend (`backend/tests/test_role_matrix.py`, Промпт 18)
  и на frontend (`src/services/PermissionService.js` покрыт Vitest-тестами, зеркалирующими ту же матрицу) —
  паритет между frontend и backend фиксируется автоматически, а не только вручную по smoke-checklist.
- **Production security hardening** — ✅ реализовано (Промпт 23): обязательный `SECRET_KEY`, secure/httpOnly/
  sameSite cookies, rate limiting на login, structured logging, `ProxyFix`, HTTPS через Caddy.
- **PostgreSQL + backup** — ✅ реализовано (Промпт 22-23): `docker-compose.yml` с Postgres, Alembic-миграциями
  и ежедневным `pg_dump`-backup sidecar.
- **CI/CD** — ✅ реализовано (Промпт 21, дополнено Промптом 24): lint+test+build для frontend/backend на каждый
  push/PR, плюс отдельный E2E workflow против docker-compose стека.
