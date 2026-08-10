from flask import Blueprint

history_bp = Blueprint("history", __name__, url_prefix="/api/history")

from app.history import routes  # noqa: E402,F401
