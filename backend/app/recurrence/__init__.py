from flask import Blueprint

recurrence_bp = Blueprint("recurrence", __name__, url_prefix="/api/recurrence-templates")

from app.recurrence import routes  # noqa: E402,F401
