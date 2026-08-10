"""
Единственный реально реализованный роут каркаса — используется фронтендом
и инфраструктурой (readiness/liveness проверки) для проверки, что backend поднят.
"""

from flask import jsonify

from app.health import health_bp


@health_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})
