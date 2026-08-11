# CHANGELOG

## v2.0.0 — 2026-08-11

Завершение перехода от frontend-only mock-MVP (v1) к полноценному приложению с реальным backend (v2).
Подводит итог Промптам 15–24.

### Главное изменение v1 → v2: dual-mode repositories

- Введена единая точка выбора реализации репозиториев (`src/repositories/index.js`), переключаемая
  переменной `VITE_API_MODE` (`mock` | `http`) без единой правки в stores/services/UI-компонентах.
- Добавлены 11 HTTP-репозиториев (`src/repositories/http/*`), зеркалирующих mock-репозитории 1:1 по контракту
  (Task, List, User, History, Recurrence, SavedView, Checklist, Note, Comment, Notification, Meeting).

### Реальный backend с ролевой моделью

- Flask-приложение (`backend/`) с blueprints на каждый ресурс, ORM/domain/DTO-слоями и мэппером
  camelCase ↔ snake_case.
- Cookie-based session-аутентификация (`Flask-Session`), CSRF-защита через `X-CSRF-Token`.
- Server-side `PermissionService` (`backend/app/services/permission_service.py`), зеркальный
  клиентскому `PermissionService.js` — источник истины для прав доступа (admin/owner/editor/viewer/assignee),
  отдающий `403 permission_denied` на нарушения.
- `POST /api/auth/change-password` для авторизованного пользователя.

### PostgreSQL и эксплуатация

- Переход с SQLite (development/testing) на PostgreSQL как production-хранилище через `docker-compose.yml`
  (`db` сервис, Alembic-миграции `alembic upgrade head` перед стартом backend).
- `backup` sidecar — ежедневный `pg_dump -Fc` с ротацией по `BACKUP_RETENTION_DAYS`.
- Production security hardening: обязательный `SECRET_KEY` (fail-fast), secure/httpOnly/sameSite cookies,
  rate limiting на `POST /api/auth/login` (`Flask-Limiter`), structured JSON logging, `ProxyFix`.
- HTTPS-терминация через Caddy (`Caddyfile.example`) с автоматическими сертификатами Let's Encrypt.

### Тесты

- Backend: `pytest` — ролевая матрица прав доступа (`backend/tests/test_role_matrix.py`), auth-эндпоинты,
  включая rate limiting и change-password.
- Frontend: `vitest` — ranking score/bubble sort, `PermissionService.js` (зеркало backend-матрицы),
  `RecurrenceService.js`.
- E2E: Playwright (`e2e/*.spec.js`) — автоматизация smoke-checklist (login/logout, 401→login, 403→откат+toast,
  Viewer-ограничения, admin-доступ, dual-mode) и silent-failure сценария (недоступность backend).

### CI/CD и Docker deployment

- `.github/workflows/frontend-ci.yml` и `backend-ci.yml` — lint + test + build на каждый push/PR.
- `.github/workflows/e2e.yml` — Playwright smoke против docker-compose стека.
- Multi-stage `Dockerfile` (frontend, nginx) и `backend/Dockerfile` (gunicorn), полный `docker-compose.yml`
  (`db` + `backend` + `frontend` + `backup`) как основной способ продового развёртывания.

### Прочее (доведено до готовности в рамках v2)

- LLM-парсер резюме встреч в задачи (`MeetingSummaryParser`) — на данный момент реализован через
  regex-эвристику по контракту `SummaryParser`; полноценная замена на LLM-провайдера остаётся в Roadmap
  (см. "Известные ограничения" в README.md).
- Real-time sync между клиентами (WebSocket/SSE) и background jobs (очередь для повторяющихся задач и
  напоминаний) в v2 не реализованы — вынесены в Roadmap.
- Отдельный audit log (шире, чем текущая `History` задач) в v2 не реализован — вынесен в Roadmap.

---

## v1.0.0 — frontend-only mock MVP

Первая версия: Vue 3 + Vite + Pinia + Vue Router + ECharts, repository/adapter pattern, все данные —
mock/localStorage, permissions только на клиенте (UX-слой без реальной защиты). Backend отсутствовал.
