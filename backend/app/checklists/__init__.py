from flask import Blueprint

checklists_bp = Blueprint("checklists", __name__, url_prefix="/api/checklist-items")

from app.checklists import routes  # noqa: E402,F401
