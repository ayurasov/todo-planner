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
  Бизнес-логика (модели SQLAlchemy поверх `backend/migrations/`, репозитории,
  сервисы) сюда сознательно не включена — это следующий шаг.
- `wsgi.py` — entrypoint для `gunicorn wsgi:app`.

## Соответствие фронтенду

- `credentials: 'include'` в apiClient.js -> `SESSION_COOKIE_*` в config.py
  + `Flask-Session` (server-side, не JWT).
- Заголовок `X-CSRF-Token` в apiClient.js -> `WTF_CSRF_HEADERS` в config.py.
- `BASE_URL = '/api'` в apiClient.js -> все blueprints зарегистрированы
  с префиксом `/api/...`.
- CORS настроен только на origin dev-сервера фронтенда (`http://localhost:5173`
  по умолчанию, см. `FRONTEND_ORIGIN` в `.env.example`).
