from flask import Blueprint

lists_bp = Blueprint("lists", __name__, url_prefix="/api/lists")

from app.lists import routes  # noqa: E402,F401
