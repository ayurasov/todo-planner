# Playwright E2E smoke-тесты (Промпт 24)

Эти тесты автоматизируют раздел **Smoke-checklist (ручная проверка)** из корневого
`README.md`. Аналогичны шагам из того раздела: login/logout, 401 → экран логина, 403 → откат
+ toast, Viewer не редактирует, admin видит /settings/users и все списки, dual-mode переключение.

## Предварительные требования

1. Запущен docker-compose стек из Промпта 22 (`docker compose up -d --build`) локально или в CI.
2. Фронтенд доступен на `http://localhost` (или `E2E_BASE_URL`, если отличается), backend — через nginx `/api/*`.
3. Выполните seed детерминированных учёток внутри backend-контейнера:

   ```bash
   docker compose exec backend python seed_e2e_data.py
   ```

   Создаёт `e2e-admin` / `e2e-owner` / `e2e-viewer` с одинаковым паролем (`E2E_SEED_PASSWORD`,
   по умолчанию `E2E-test-pass-123!`) и список `E2E: Smoke` (owner=e2e-owner, viewer=e2e-viewer).
   Скрипт отказывается запускаться в `FLASK_ENV=production`.

4. Установите Playwright-браузеры (один раз):

   ```bash
   npm install
   npx playwright install --with-deps chromium
   ```

## Запуск

```bash
# против docker-compose стека на http://localhost (дефолт)
npm run e2e

# если стек опубликован на другом адресе/порту
E2E_BASE_URL=http://localhost:8080 npm run e2e

# интерактивный UI-режим для отладки
npm run e2e:ui
```

## Структура

- `e2e/fixtures.js` — шаредные утилиты (логин/логаут через UI, учётные данные e2e-admin/owner/viewer).
- `e2e/auth.spec.js` — шаги 1–3 smoke-checklist: login/logout, повторный заход без сессии → `/login`.
- `e2e/permissions.spec.js` — шаги 4–6: 403 → откат+toast, Viewer не редактирует, admin видит /settings/users и все списки.
- `e2e/dual-mode.spec.js` — шаг 7: базовая проверка, что сборка в http-режиме работает без правкок `src/` (dual-mode сам по себе проверяется в части mock отдельными Vitest-тестаци mock-репозиториев, а здесь проверяется, что http-сборка видит реальные backend-данные, а не mock-seed).
- `e2e/network-failure.spec.js` — проверка silent-failure сценария: недоступность backend (не 401/403) должна давать понятную ошибку, а не белый экран/вечный спиннер.

## Ограничения

- Тесты не заменяют шаги 8–9 smoke-checklist (Editor/Owner управление участниками/удаление списка) --
  они требуют `seed_demo_data.py` с недетерминированными паролями; для CI остаются ручными пок в беклоге.
- Сетевой offline-тест эмулирует недоступность через `page.route()` (abort), а не остановку backend-контейнера,
  чтобы тест оставался быстрым и не требовал docker внутри теста.
