from flask import Blueprint

saved_views_bp = Blueprint("saved_views", __name__, url_prefix="/api/saved-views")

from app.saved_views import routes  # noqa: E402,F401
