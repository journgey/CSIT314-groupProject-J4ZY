from flask import Blueprint, request, jsonify
from backend.controllers.requests_search_controller import RequestsSearchController
from backend.repositories.requests_search_repository import RequestsSearchRepository
from backend.db_session import get_db
from backend.auth import login_required, require_role

requests_search_bp = Blueprint("requests_search", __name__)

def _service():
    repo = RequestsSearchRepository(get_db())
    return RequestsSearchController(repo)

@requests_search_bp.get("/search")
def search_requests():
    service = _service()
    filters = {
            "category_id": request.args.get("category_id", type=int),
            "region_id": request.args.get("region_id", type=int),
            "district_id": request.args.get("district_id", type=int),
            "created_at": request.args.get("created_at", type=str),
            "start_at": request.args.get("start_at", type=str),
            "end_at": request.args.get("end_at", type=str),
            "status": request.args.get("status", type=str),            
            "pin_id": request.args.get("pin_id", type=int),            
            "csr_id": request.args.get("csr_id", type=int),            
            "limit": request.args.get("limit", default=20, type=int),
            "offset": request.args.get("offset", default=0, type=int),
            "sort": request.args.get("sort", default="created_at", type=str),
            "order": request.args.get("order", default="desc", type=str),
        }

    filters = {k: v for k, v in filters.items() if v is not None}

    results = service.search_requests(filters)
    return jsonify(results), 200

@requests_search_bp.get("/history")
@login_required
@require_role("PIN", "CSR")
def search_history():
    svc = _service()
    role_scope = (request.args.get("role_scope") or g.current_user["role"]).lower()

    filters = {
        "date_from": request.args.get("date_from"),
        "date_to": request.args.get("date_to"),
        "category_id": request.args.get("category_id", type=int),
        "only_with_feedback": request.args.get("only_with_feedback") == "true",
        "limit": request.args.get("limit", default=20, type=int),
        "offset": request.args.get("offset", default=0, type=int),
        "sort": request.args.get("sort", default="end_at", type=str),
        "order": request.args.get("order", default="desc", type=str),
    }
    filters = {k: v for k, v in filters.items() if v is not None}

    if role_scope == "pin":
        results = svc.search_pin_history(g.current_user["id"], filters)
    elif role_scope == "csr":
        results = svc.search_csr_history(g.current_user["id"], filters)
    else:
        return jsonify({"error": "Invalid role_scope"}), 400

    return jsonify(results), 200