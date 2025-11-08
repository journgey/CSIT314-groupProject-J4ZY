from flask import Blueprint, request, jsonify, g
from backend.auth import login_required, require_role
from backend.controllers.requests_controller import RequestsController
from backend.repositories.requests_repository import RequestsRepository
from backend.db_session import get_db

requests_bp = Blueprint("requests_bp", __name__)

def _service() -> RequestsController:
    repo = RequestsRepository(get_db())
    return RequestsController(repo)

@requests_bp.get("/")
@login_required
@require_role("PIN", "CSR", "PlatformManager")
def list_requests():
    service = _service()
    filters = {
        "status": request.args.get("status"),
        "pin_id": request.args.get("pin_id", type=int),
        "csr_id": request.args.get("csr_id", type=int),
        "category_id": request.args.get("category_id", type=int),
        "district_id": request.args.get("district_id", type=int),
    }
    data = service.list_requests({k: v for k, v in filters.items() if v is not None and v != ""})
    return jsonify(data), 200

@requests_bp.get("/<int:req_id>")
@login_required
@require_role("PIN", "CSR", "PlatformManager")
def get_request(req_id: int):
    service = _service()
    item = service.get_request_by_id(req_id)
    if not item:
        return jsonify({"error": "Request not found"}), 404
    return jsonify(item), 200

@requests_bp.post("/")
@login_required
@require_role("PIN")
def create_request():
    service = _service()
    payload = (request.get_json() or {})
    created = service.create_request(
        payload,
        acting_user_id=g.current_user["id"],
        acting_role=g.current_user["role"],
    )
    return jsonify(created), 201

@requests_bp.put("/<int:req_id>")
@login_required
@require_role("PIN")
def update_request(req_id: int):
    service = _service()
    payload = (request.get_json() or {})
    updated = service.update_request(
        req_id,
        payload,
        acting_user_id=g.current_user["id"],
        acting_role=g.current_user["role"],
    )
    if not updated:
        return jsonify({"error": "Request not found"}), 404
    return jsonify(updated), 200

@requests_bp.delete("/<int:req_id>")
@login_required
@require_role("PIN", "PlatformManager")
def delete_request(req_id: int):
    service = _service()
    ok = service.delete_request(
        req_id,
        acting_user_id=g.current_user["id"],
        acting_role=g.current_user["role"],
    )
    if not ok:
        return jsonify({"error": "Request not found"}), 404
    return jsonify({"message": "Request deleted"}), 200
