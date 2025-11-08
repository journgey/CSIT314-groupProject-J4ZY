from flask import Blueprint, request, jsonify, g
from backend.db_session import get_db
from backend.repositories.notifications_repository import NotificationsRepository
from backend.controllers.notifications_controller import NotificationsController
from backend.repositories.requests_repository import RequestsRepository
from backend.repositories.accounts_repository import AccountsRepository
from backend.auth import login_required, require_role

notifications_bp = Blueprint("notifications_bp", __name__)

def _service() -> NotificationsController:
    conn = get_db()
    repo = NotificationsRepository(conn)
    return NotificationsController(repo)

@notifications_bp.route("/", methods=["GET"])
@login_required
@require_role("PIN", "CSR", "PlatformManager")
def list_notifications():
    unread_str = request.args.get("unread", "").lower()
    unread_only = unread_str in ("1", "true", "yes")
    items = _service().list_for_user(user_id=g.current_user["id"], unread_only=unread_only)
    return jsonify({"items": items}), 200

@notifications_bp.route("/<int:notification_id>/read", methods=["PUT"])
@login_required
@require_role("PIN", "CSR", "PlatformManager")
def mark_read(notification_id: int):
    item = _service().mark_read(notification_id=notification_id, current_user_id=g.current_user["id"])
    return jsonify(item), 200

@notifications_bp.route("/<int:notification_id>/unread", methods=["PUT"])
@login_required
@require_role("PIN", "CSR", "PlatformManager")
def mark_unread(notification_id: int):
    item = _service().mark_unread(notification_id=notification_id, current_user_id=g.current_user["id"])
    return jsonify(item), 200

@notifications_bp.delete("/<int:notification_id>")
@login_required
@require_role("PIN", "CSR", "PlatformManager")
def delete_notification(notification_id: int):
    item = _service().delete(notification_id=notification_id, current_user_id=g.current_user["id"])
    return jsonify(item), 200

@notifications_bp.post("/actions/request-accepted")
@login_required
@require_role("CSR")
def notify_request_accepted():
    payload = request.get_json(silent=True) or {}
    request_id = payload.get("request_id")
    if not isinstance(request_id, int):
        return jsonify({"error": "request_id is required"}), 400

    conn = get_db()
    req = RequestsRepository(conn).get_request_by_id(request_id)
    if not req:
        return jsonify({"error": "Request not found"}), 404
    if req.get("csr_id") != g.current_user["id"]:
        return jsonify({"error": "Forbidden"}), 403

    actor = AccountsRepository(conn).get_account_by_id(g.current_user["id"])
    out = _service().create_for_csr_accepted_request(
        pin_user_id=req["pin_id"],
        actor_name=actor["name"],
        request_title=req["title"],
        request_id=req["id"],
        actor_id=g.current_user["id"],
    )
    return jsonify(out), 201

@notifications_bp.post("/actions/request-cancelled")
@login_required
@require_role("PIN")
def notify_request_cancelled():
    payload = request.get_json(silent=True) or {}
    request_id = payload.get("request_id")
    if not isinstance(request_id, int):
        return jsonify({"error": "request_id is required"}), 400

    conn = get_db()
    req = RequestsRepository(conn).get_request_by_id(request_id)
    if not req:
        return jsonify({"error": "Request not found"}), 404

    if req.get("pin_id") != g.current_user["id"]:
        return jsonify({"error": "Forbidden"}), 403

    csr_id = req.get("csr_id")
    if not csr_id:
        return ("", 204)

    actor = AccountsRepository(conn).get_account_by_id(g.current_user["id"])
    out = _service().create_for_pin_deleted_request(
        csr_user_id=csr_id,
        actor_name=actor["name"],
        request_title=req["title"],
        request_id=req["id"],
        actor_id=g.current_user["id"],
    )
    return jsonify(out), 201