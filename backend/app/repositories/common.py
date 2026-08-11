"""
Общие вспомогательные функции для repositories-слоя: генерация id и
таймстампов в том же формате, что уже исцами применяется в app.auth.seed
(UUID4 для id, timezone-aware UTC datetime для БД).
"""

import uuid
from datetime import datetime, timezone


def new_id() -> str:
    return str(uuid.uuid4())


def now_iso():
    return datetime.now(timezone.utc)
