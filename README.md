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
- `src/repositories` — контракты (интерфейсы) + mock-реализации с персистентностью в localStorage.
  Единая точка внедрения — `src/repositories/index.js`. При переходе на v2 меняется только этот файл.
- `src/integrations/calendar` — абстракция CalendarProvider + mock-реализация (Exchange-подобная, заглушка).
- `src/services` — PermissionService, HistoryService, RecurrenceService.
- `src/stores` — Pinia store'ы (users, lists, tasks, view, history, recurrence, calendar).
- `src/components` — UI-компоненты (задачи, чарты, общие элементы).
- `src/views` — экраны: My Tasks, Team Tasks, List View, Recurring, History, Settings.

## Данные

В v1 данные — mock, хранятся в `localStorage` (переживают обновление страницы, решение по допущению #3).
Чтобы сбросить к seed-данным — очистите localStorage браузера (ключи с префиксом `todo-planner:v1:`).

## Ranking score / "вываливание вверх" / "исчезание"

См. `src/domain/ranking/rankingScore.js` — прозрачный алгоритм с явным разложением по факторам
(overdue, dueSoon, recency, assignedToMe, pinned, priority). Веса зафиксированы как константы (RANKING_WEIGHTS).
