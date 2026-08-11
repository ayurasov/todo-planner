"""Инициализация Flask extensions в одном месте."""

from flask_cors import CORS
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


db = SQLAlchemy()
sess = Session()
cors = CORS()
csrf = CSRFProtect()
migrate = Migrate(compare_type=True)
# key_func=get_remote_address -- лимит считается по IP клиента (X-Forwarded-For
# учитывается автоматически, если nginx/reverse-proxy настроен корректно, см.
# ProxyFix в app/__init__.py). default_limits не задаются здесь -- лимиты
# навешиваются точечно на конкретные view (см. app/auth/routes.py), чтобы не
# ограничивать остальные, уже аутентифицированные, эндпоинты.
limiter = Limiter(key_func=get_remote_address)
