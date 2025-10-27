from flask import Blueprint, request, jsonify
from repositories.requests_repository import RequestsRepository
from services.requests_service import RequestsService
from db_session import get_db

requests_bp = Blueprint("requests", __name__)

def _service():
    repo = RequestsRepository(get_db())
    return RequestsService(repo)

@requests_bp.get("/")
def list_requests():
    # Simple filters: status, pin_id, csr_id, category_id, district_id
    service = _service()
    filters = {
        "status": request.args.get("status"),
        "pin_id": request.args.get("pin_id", type=int),
        "csr_id": request.args.get("csr_id", type=int),
        "category_id": request.args.get("category_id", type=int),
        "district_id": request.args.get("district_id", type=int),
    }
    data = service.list_requests({k: v for k, v in filters.items() if v is not None})
    return jsonify(data), 200

@requests_bp.get("/<int:req_id>")
def get_request(req_id: int):
    """Get a single request by ID."""
    service = _service()
    item = service.get_request_by_id(req_id)
    if not item:
        return jsonify({"error": "Request not found"}), 404
    return jsonify(item), 200

@requests_bp.post("/")
def create_request():
    """Create a new request."""
    service = _service()
    payload = request.get_json() or {}
    created = service.create_request(payload)
    return jsonify(created), 201

@requests_bp.put("/<int:req_id>")
def update_request(req_id: int):
    """Update an existing request."""
    service = _service()
    payload = request.get_json() or {}
    updated = service.update_request(req_id, payload)
    if not updated:
        return jsonify({"error": "Request not found"}), 404
    return jsonify(updated), 200

@requests_bp.delete("/<int:req_id>")
def delete_request(req_id: int):
    """Delete a request."""
    service = _service()
    ok = service.delete_request(req_id)
    if not ok:
        return jsonify({"error": "Request not found"}), 404
    return jsonify({"message": "Request deleted"}), 200
