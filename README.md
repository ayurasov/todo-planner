# Todo Planner — Frontend-only MVP v1

Веб-планировщик задач на Vue 3 + Vite + Pinia + Vue Router + ECharts.
Реализован по утверждённой архитектуре (repository/adapter pattern, готовый к переходу на Flask+SQLite v2 без переписывания UI).

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
