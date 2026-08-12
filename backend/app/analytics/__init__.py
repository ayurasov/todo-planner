from flask import Blueprint

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")

from app.analytics import routes  # noqa: E402,F401
