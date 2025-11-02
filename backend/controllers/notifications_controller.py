from flask import Blueprint, request, jsonify, g
from backend.db_session import get_db
from backend.repositories.notifications_repository import NotificationsRepository
from backend.services.notifications_service import NotificationsService
from backend.auth import login_required, require_role

notifications_bp = Blueprint("notifications_bp", __name__)

def _service() -> NotificationsService:
    """
    Factory: inject DB connection and wire Repo -> Service.
    """
    conn = get_db()
    repo = NotificationsRepository(conn)
    return NotificationsService(repo)

# ---------- List my notifications ----------
@notifications_bp.route("/", methods=["GET"])
@login_required
@require_role("PIN", "CSR", "PlatformManager")
def list_notifications():
    try:
        unread_str = request.args.get("unread", "").lower()
        unread_only = unread_str in ("1", "true", "yes")
        items = _service().list_for_user(user_id=g.current_user["id"], unread_only=unread_only)
        return jsonify({"items": items}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

# ---------- Mark as read ----------
@notifications_bp.route("/<int:notification_id>/read", methods=["PUT"])
@login_required
@require_role("PIN", "CSR", "PlatformManager")
def mark_read(notification_id: int):
    try:
        item = _service().mark_read(notification_id=notification_id, current_user_id=g.current_user["id"])
        return jsonify(item), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

# ---------- Mark as unread ----------
@notifications_bp.route("/<int:notification_id>/unread", methods=["PUT"])
@login_required
@require_role("PIN", "CSR", "PlatformManager")
def mark_unread(notification_id: int):
    try:
        item = _service().mark_unread(notification_id=notification_id, current_user_id=g.current_user["id"])
        return jsonify(item), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

# ---------- Delete ----------
@notifications_bp.route("/<int:notification_id>", methods=["DELETE"])
@login_required
@require_role("PIN", "CSR", "PlatformManager")
def delete_notification(notification_id: int):
    try:
        item = _service().delete(notification_id=notification_id, current_user_id=g.current_user["id"])
        return jsonify(item), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
