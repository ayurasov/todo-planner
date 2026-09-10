# По Делу — Todo Planner v1.0.3

Веб-система управления задачами, встречами, подвстречами, регулярными встречами, списками, комментариями, уведомлениями, историей изменений и аналитикой.

В интерфейсе версия приложения отображается в меню: **По Делу — Версия 1.0.3**. Источник версии — поле `version` в корневом `package.json`.

## Возможности

- личные, командные и списочные задачи;
- назначение исполнителей и контроль прав доступа;
- встречи и подвстречи, включая регулярные встречи;
- отображение назначенных задач из встреч без раскрытия недоступной встречи;
- подзадачи, чек-листы, заметки и комментарии;
- редактирование и удаление комментариев с проверкой авторства и ролей;
- фильтры по статусу, исполнителю, срокам и недавно выполненным задачам;
- текстовый поиск в задачах команды;
- группировка задач по состоянию и контексту встречи;
- история изменений, уведомления и сохранённые представления;
- режимы `mock` для автономной разработки и `http` для Flask backend;
- PostgreSQL в production, SQLite для development/testing;
- Docker Compose, миграции Alembic, резервные копии и HTTPS через reverse proxy.

## Что нового в 1.0.3

- комментарии можно редактировать и удалять с учётом прав пользователя;
- сохранено форматирование комментариев, аналогичное описанию задачи;
- добавлены компактные фильтры `7д` и `14д` в «Задачах команды»;
- фильтр исполнителей строится по реально видимым задачам;
- в контексте встречи учитываются участники, исполнители задач и исполнители доступных подзадач;
- выпадающий список исполнителей закрывается при клике за его пределами;
- список остаётся открытым при последовательном выборе нескольких исполнителей;
- добавлены исправления работы с задачами встреч и подвстреч.

Полная история изменений находится в [`docs/versions.md`](docs/versions.md). Краткая история также поддерживается в [`CHANGELOG.md`](CHANGELOG.md).

## Стек

### Frontend

- Vue 3;
- Vite;
- Pinia;
- Vue Router;
- Apache ECharts;
- Vitest и Playwright;
- ESLint 9 и `eslint-plugin-vue`.

Версии frontend-зависимостей фиксируются в `package.json` и `package-lock.json`. Текущая версия приложения — `1.0.3`.

### Backend

- Python 3.12;
- Flask;
- Gunicorn;
- Flask-SQLAlchemy и SQLAlchemy;
- Flask-Session;
- Flask-WTF / CSRFProtect;
- Flask-CORS;
- Flask-Limiter;
- Pydantic DTO;
- Alembic;
- PostgreSQL в production, SQLite в development и тестах;
- pytest и Ruff.

### Runtime

- Docker и Docker Compose;
- Nginx для frontend SPA и проксирования `/api`;
- Caddy как внешний TLS reverse proxy;
- PostgreSQL 16 Alpine;
- ежедневный `pg_dump -Fc` через backup-контейнер.

## Быстрый запуск через Docker

### Требования

- Docker Engine с Compose V2;
- свободные порты `80` и, при настройке HTTPS, `443`;
- для production — домен, направленный на сервер;
- для локальной разработки без Docker — Node.js и Python 3.12.

### Локальный Docker-запуск

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
# вставьте результат в SECRET_KEY
# замените POSTGRES_PASSWORD и DATABASE_URL на согласованные значения

docker compose up -d --build
docker compose ps
```

После запуска:

- приложение: `http://localhost`;
- health-check: `http://localhost/api/health`;
- backend внутри Compose-сети: `http://backend:5000`;
- логи: `docker compose logs -f backend`.

Backend перед запуском приложения ожидает готовность PostgreSQL и применяет миграции `alembic upgrade head`. Не удаляйте volume базы при обычном обновлении.

## Что находится в контейнерах

- `db` — PostgreSQL 16 Alpine, данные в volume `db_data`;
- `backend` — Python 3.12 slim, Flask-приложение под Gunicorn, миграции применяются entrypoint-скриптом;
- `frontend` — multi-stage Vite build и Nginx runtime, Nginx отдаёт SPA и проксирует `/api` в backend;
- `backup` — PostgreSQL-клиент в контейнере `postgres:16-alpine`, ежедневный `pg_dump -Fc` и очистка старых файлов.

Внешний порт backend намеренно не нужен: production-трафик проходит через frontend Nginx и внешний reverse proxy.

## Преднастройка и первоначальная настройка

1. Скопируйте `.env.example` в `.env`.
2. Задайте уникальные `SECRET_KEY`, `POSTGRES_PASSWORD` и `DATABASE_URL`.
3. Укажите публичный `FRONTEND_ORIGIN`.
4. Запустите Compose.
5. Проверьте `/api/health` и логи backend.
6. При пустой базе сохраните временные пароли первоначальных пользователей из лога: они выводятся один раз.
7. Смените пароль через интерфейс или `POST /api/auth/change-password`.
8. Проверьте роли и участников перед выдачей пользователям production-доступа.

Для демонстрационных данных backend предоставляет `seed_demo_data.py`, а для E2E — `seed_e2e_data.py`. Не запускайте seed-скрипты на production-базе.

## Переменные окружения

Актуальный шаблон находится в `.env.example`.

| Переменная | Назначение |
| --- | --- |
| `VITE_API_MODE` | `mock` для localStorage или `http` для Flask API. |
| `VITE_API_BASE_URL` | URL API; для Compose обычно `/api`. |
| `POSTGRES_USER` | Пользователь PostgreSQL. |
| `POSTGRES_PASSWORD` | Пароль PostgreSQL; замените placeholder. |
| `POSTGRES_DB` | Имя базы данных. |
| `DATABASE_URL` | SQLAlchemy URL, например `postgresql+psycopg2://user:pass@db:5432/db`. |
| `SECRET_KEY` | Обязательный секрет Flask-сессий и CSRF. Не используйте значение из примера. |
| `FRONTEND_ORIGIN` | Публичный origin, например `https://todo.example.com`. |
| `SESSION_COOKIE_SAMESITE` | Обычно `Lax`; `None` требует HTTPS. |
| `SESSION_COOKIE_SECURE` | В production — `true`; временно `false` допустимо только для локального HTTP. |
| `RATELIMIT_STORAGE_URI` | Хранилище лимитов, по умолчанию `memory://`. Для нескольких реплик используйте Redis. |
| `LOGIN_RATE_LIMIT` | Лимит login, например `10 per minute;50 per hour`. |
| `BACKUP_RETENTION_DAYS` | Срок хранения dump-файлов, по умолчанию 14 дней. |

Не коммитьте `.env`, реальные пароли, ключи и backup-файлы. Используйте секрет-хранилище CI/CD или менеджер секретов сервера.

## Режимы запуска

### Mock-режим

```bash
npm ci
cp .env.example .env
# VITE_API_MODE=mock
npm run dev
```

Backend не нужен. Данные хранятся в `localStorage`. Этот режим предназначен для UI-разработки и демонстраций: клиентские проверки прав не являются защитой данных.

### HTTP-режим с локальным backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
export FLASK_ENV=development
python wsgi.py
```

В отдельном терминале:

```bash
npm ci
# VITE_API_MODE=http
# VITE_API_BASE_URL=http://localhost:5000/api
npm run dev
```

Frontend доступен на `http://localhost:5173`, backend — на `http://localhost:5000`. В HTTP-режиме используются cookie-сессии и CSRF-токен, JWT не используется.

## Production и HTTPS

Не публикуйте frontend Nginx напрямую в Internet без TLS. Рекомендуемая схема:

`Internet → Caddy :443 → frontend Nginx :80 → backend :5000`, а backend подключается к PostgreSQL.

Скопируйте `Caddyfile.example` в `Caddyfile`, замените домен и подключите Caddy:

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

Caddy получает и продлевает сертификаты Let's Encrypt. DNS домена должен указывать на сервер, а порты `80` и `443` должны быть доступны для ACME-проверки.

В `Caddyfile` рекомендуется включить:

- `reverse_proxy frontend:80`;
- gzip/encode;
- HSTS после окончательной проверки HTTPS;
- `X-Content-Type-Options: nosniff`;
- `X-Frame-Options: DENY`;
- `Referrer-Policy: strict-origin-when-cross-origin`.

В production включите `SESSION_COOKIE_SECURE=true`, используйте реальный `SECRET_KEY` и укажите HTTPS-origin в `FRONTEND_ORIGIN`. Backend применяет `ProxyFix` для корректной обработки `X-Forwarded-*`.

## База данных и миграции

- development: SQLite-файл, если не задан `DATABASE_URL`;
- testing: in-memory SQLite через `TestingConfig`;
- production: PostgreSQL, рекомендуется URL `postgresql+psycopg2://...`.

Команды миграций:

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
alembic history
alembic downgrade -1
alembic revision --autogenerate -m "describe change"
```

Перед production-деплоем создайте backup и примените миграции. Не используйте `db.create_all()` как замену миграциям в production.

## Резервное копирование и восстановление

Сервис `backup` создаёт ежедневный custom-format dump PostgreSQL в volume `db_backups` и удаляет файлы старше `BACKUP_RETENTION_DAYS`.

```bash
# разовый backup
docker compose exec backup sh -c 'FILE=/backups/manual_$(date -u +%Y%m%dT%H%M%SZ).dump && pg_dump -Fc -f "$FILE" && echo "$FILE"'

# посмотреть volume
docker volume ls | grep backup

# восстановить в отдельную пустую БД
docker compose exec -T db createdb -U "$POSTGRES_USER" restore_db
docker compose exec -T backup sh -c 'pg_restore -d "$PGDATABASE" /backups/<file>.dump'
```

Перед восстановлением остановите backend или переведите систему в режим обслуживания. Проверьте, что dump читается, выполните пробное восстановление в отдельную БД и только затем заменяйте production-данные. Для настоящей эксплуатации дополнительно нужна offsite-копия и регулярный restore drill: Docker volume на том же сервере не защищает от потери сервера.

Для SQLite development/test используйте snapshot-копии файла базы на уровне хоста.

## Логирование и security controls

Backend пишет operational-логи в stdout в JSON-lines формате: timestamp, level, logger, message, HTTP method, path, remote address и user id, если они известны.

Включены базовые controls:

- обязательный `SECRET_KEY` с fail-fast при placeholder/пустом значении;
- server-side cookie sessions, `HttpOnly`, `Secure` и настраиваемый `SameSite`;
- CSRF-защита mutating-запросов через `X-CSRF-Token`;
- rate limiting login;
- проверка авторизации на API routes;
- backend `PermissionService` как источник истины для прав;
- стабильные ответы `401` и `403 permission_denied`;
- HTTPS termination через Caddy и security headers;
- отсутствие `password_hash` в DTO пользователей;
- запрет хранения секретов и backup-файлов в Git.

Frontend permission checks используются для UX, но не заменяют backend-проверки. При нескольких backend-инстансах вынесите rate-limit storage в Redis и централизуйте сбор логов.

## Обновление после новой версии

1. Прочитайте release notes и проверьте требования к миграциям.
2. Сделайте и проверьте backup.
3. Скачайте нужный tag/commit или обновите рабочую ветку.
4. Проверьте `.env` и секреты; не перезаписывайте production `.env` шаблоном.
5. Пересоберите образы:

```bash
git fetch --tags
git checkout <version-or-tag>
docker compose config
docker compose up -d --build
docker compose ps
docker compose logs --tail=200 backend
curl -f https://todo.example.com/api/health
```

6. Убедитесь, что миграции завершились, health-check зелёный и вход работает.
7. Выполните smoke-проверку задач, встреч, комментариев, фильтров и прав.
8. При проблеме остановите rollout, сохраните логи и восстановите backup только по утверждённому плану отката.

Версия интерфейса меняется в `package.json`; release notes поддерживаются в `docs/versions.md`, а GitHub Release должен использовать соответствующий tag, например `v1.0.3`.

## Сборка и тестирование

### Frontend

```bash
npm ci
npm run lint
npm run test
npm run build
npm run preview
```

`npm run test` запускает Vitest. Покрываются ranking/bubble sorting, матрица frontend permissions, recurrence и чистая бизнес-логика.

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
ruff check .
pytest
```

Backend-тесты используют in-memory SQLite. Проверяются auth/CSRF, роли и permissions, CRUD/DTO и критические правила доступа.

### E2E

```bash
docker compose up -d --build
docker compose exec backend python seed_e2e_data.py
npm ci
npx playwright install --with-deps chromium
npm run e2e
```

Playwright проверяет базовый login/logout, 401/403, CSRF, admin-доступ, dual-mode и сетевые ошибки. E2E следует запускать против отдельной тестовой базы.

## CI/CD

Workflow находятся в `.github/workflows/`:

- frontend CI: install, lint, Vitest и build;
- backend CI: Ruff и pytest;
- E2E: Playwright против Docker Compose.

Для защиты `main` включите GitHub branch protection и обязательные успешные status checks перед merge. Workflow сами по себе не блокируют merge, пока правило не включено в настройках репозитория.

## Структура репозитория

```text
.
├── src/
│   ├── components/       # UI-компоненты
│   ├── domain/           # чистые сущности и ranking
│   ├── integrations/      # интеграции календаря
│   ├── repositories/      # mock/http контракты
│   ├── services/          # права, история, recurrence
│   ├── stores/            # Pinia stores
│   ├── views/             # экраны приложения
│   └── router/            # маршрутизация и guards
├── backend/
│   ├── app/               # Flask blueprints, domain, DTO, repositories
│   ├── migrations/        # Alembic migrations
│   ├── tests/             # pytest
│   ├── config.py          # environment profiles
│   └── wsgi.py            # Gunicorn entrypoint
├── e2e/                   # Playwright smoke tests
├── public/                # статические ресурсы
├── Dockerfile             # frontend build + Nginx runtime
├── backend/Dockerfile     # backend production image
├── docker-compose.yml     # db/backend/frontend/backup
├── nginx.conf             # SPA и API proxy
├── Caddyfile.example      # HTTPS reverse proxy
├── .env.example           # шаблон конфигурации
├── docs/versions.md       # versioned release notes
└── package.json           # scripts и версия приложения
```

## API и аутентификация

API имеет префикс `/api`. Основные группы endpoints: `/health`, `/auth`, `/users`, `/lists`, `/tasks`, `/meetings`, `/recurrence-templates`, `/comments`, `/checklist-items`, `/notes`, `/history`, `/notifications` и `/saved-views`.

Аутентификация cookie-based:

1. frontend получает CSRF через `GET /api/auth/csrf-token`;
2. отправляет `POST /api/auth/login` с cookie и `X-CSRF-Token`;
3. получает текущего пользователя через `GET /api/auth/me`;
4. для POST/PATCH/DELETE передаёт CSRF-заголовок;
5. завершает сессию через `POST /api/auth/logout`.

## Ограничения

- real-time синхронизация через WebSocket/SSE не подключена;
- фоновые очереди для recurrence и уведомлений не подключены;
- parser резюме встречи использует эвристики, а не LLM;
- отдельный неизменяемый audit log шире истории задач отсутствует;
- backup sidecar не заменяет offsite-репликацию и restore drill;
- вложения задач остаются отдельным незавершённым направлением;
- mock-режим не обеспечивает серверную защиту.

## Лицензирование и внутреннее использование

Репозиторий содержит внутреннюю систему планирования. Перед внешней публикацией необходимо отдельно определить лицензию, политику обработки персональных данных и правила хранения production-логов/backup-файлов.
