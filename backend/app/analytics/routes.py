"""
Blueprint 'analytics' -- на данный момент содержит только один эндпойнт:
GET /api/analytics/scope, который отдаёт AnalyticsView.vue список user_id,
чью аналитику текущему пользователю разрешено видеть (см.
app.services.permission_service.get_analytics_scope_user_ids).

Раньше страница аналитики строила статистику по всем пользователям, которых
возвращал GET /api/users (после фильтрации по isActive) без какого-либо ACL --
обычный сотрудник видел полную аналитику по всей компании. isUnrestricted=True
означает "без ограничений" (глобальный admin) -- тогда userIds можно
игнорировать на фронтенде.
"""

from flask import jsonify

from app.analytics import analytics_bp
from app.auth.security import current_user_id
from app.services.permission_service import permission_service


@analytics_bp.route("/scope", methods=["GET"])
def get_analytics_scope(**kwargs):
    user_id = current_user_id()
    scope_ids = permission_service.get_analytics_scope_user_ids(user_id)
    if scope_ids is None:
        return jsonify({"isUnrestricted": True, "userIds": []})
    return jsonify({"isUnrestricted": False, "userIds": sorted(scope_ids)})
