"""
Blueprint 'uploads' -- статическая раздача файлов, загруженных через
POST /api/users/:id/avatar (см. app.users.routes). Файлы физически лежат
в backend/instance/uploads/avatars/<filename> (instance-папка не версионируется
и переживает дебв поверх volume) и раздаются по GET /api/uploads/avatars/<filename>.

Раздача через отдельный Flask-роут (а не send_from_directory на статике
приложения) даёт единую точку для будущих проверок доступа/кэш-заголовков,
без необходимости настраивать статический alias в nginx уже сейчас (см. README, раздел deployment).
"""

import os

from flask import current_app, send_from_directory

from app.uploads import uploads_bp

AVATARS_SUBDIR = "avatars"


def avatars_dir():
    upload_root = os.path.join(current_app.instance_path, "uploads", AVATARS_SUBDIR)
    os.makedirs(upload_root, exist_ok=True)
    return upload_root


@uploads_bp.route("/avatars/<string:filename>", methods=["GET"])
def get_avatar(filename, **kwargs):
    return send_from_directory(avatars_dir(), filename)
