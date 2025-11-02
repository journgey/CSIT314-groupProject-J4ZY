from flask import Blueprint, request, jsonify, g
from backend.auth import login_required, require_role
from backend.services.requests_service import RequestsService
from backend.repositories.requests_repository import RequestsRepository
from backend.db_session import get_db

# NOTE: url_prefix is set in app.py (e.g., "/api/requests")
requests_bp = Blueprint("requests_bp", __name__)

def _service() -> RequestsService:
    repo = RequestsRepository(get_db())
    return RequestsService(repo)

# ----- Read -----
@requests_bp.get("/")
@login_required
@require_role("PIN", "CSR", "PlatformManager")
def list_requests():
    """
    Optional filters:
      - status (pending|accepted|completed|expired)
      - pin_id, csr_id, category_id, district_id
    Source: v_requests_status (computed status)
    """
    svc = _service()
    filters = {
        "status": request.args.get("status"),
        "pin_id": request.args.get("pin_id", type=int),
        "csr_id": request.args.get("csr_id", type=int),
        "category_id": request.args.get("category_id", type=int),
        "district_id": request.args.get("district_id", type=int),
    }
    data = svc.list_requests({k: v for k, v in filters.items() if v is not None and v != ""})
    return jsonify(data), 200

@requests_bp.get("/<int:req_id>")
@login_required
@require_role("PIN", "CSR", "PlatformManager")
def get_request(req_id: int):
    svc = _service()
    item = svc.get_request_by_id(req_id)
    if not item:
        return jsonify({"error": "Request not found"}), 404
    return jsonify(item), 200

# ----- Create (PIN only) -----
@requests_bp.post("/")
@login_required
@require_role("PIN")
def create_request():
    svc = _service()
    payload = (request.get_json() or {})
    try:
        created = svc.create_request(
            payload,
            acting_user_id=g.current_user["id"],
            acting_role=g.current_user["role"],
        )
        return jsonify(created), 201
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

# ----- Update (PIN owner only) -----
@requests_bp.put("/<int:req_id>")
@login_required
@require_role("PIN")
def update_request(req_id: int):
    svc = _service()
    payload = (request.get_json() or {})
    try:
        updated = svc.update_request(
            req_id,
            payload,
            acting_user_id=g.current_user["id"],
            acting_role=g.current_user["role"],
        )
        if not updated:
            return jsonify({"error": "Request not found"}), 404
        return jsonify(updated), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

# ----- Delete (PIN owner OR PlatformManager) -----
@requests_bp.delete("/<int:req_id>")
@login_required
@require_role("PIN", "PlatformManager")
def delete_request(req_id: int):
    svc = _service()
    try:
        ok = svc.delete_request(
            req_id,
            acting_user_id=g.current_user["id"],
            acting_role=g.current_user["role"],
        )
        if not ok:
            return jsonify({"error": "Request not found"}), 404
        return jsonify({"message": "Request deleted"}), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
