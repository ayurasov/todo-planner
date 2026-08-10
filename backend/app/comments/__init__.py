from flask import Blueprint

comments_bp = Blueprint("comments", __name__, url_prefix="/api/comments")

from app.comments import routes  # noqa: E402,F401
