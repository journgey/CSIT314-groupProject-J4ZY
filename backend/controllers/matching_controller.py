from flask import Blueprint, request, jsonify, g
from backend.auth import login_required, require_role
from backend.db_session import get_db
from backend.repositories.requests_repository import RequestsRepository
from backend.repositories.accounts_repository import AccountsRepository
from backend.services.matching_service import MatchingService

matching_bp = Blueprint("matching", __name__)  # url_prefix는 app.py에서 "/api"로 등록

def _service():
    conn = get_db()
    return MatchingService(
        requests_repo=RequestsRepository(conn),
        accounts_repo=AccountsRepository(conn),
    )

@matching_bp.put("/requests/<int:request_id>/accept")
@login_required
@require_role("CSR")
def accept_request(request_id: int):
    try:
        out = _service().accept_request(csr_id=g.current_user["id"], request_id=request_id)
        return jsonify(out), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@matching_bp.put("/requests/<int:request_id>/assign")
@login_required
@require_role("CSR")
def assign_volunteers(request_id: int):
    try:
        payload = request.get_json(silent=True) or {}
        volunteers = payload.get("volunteers", [])  # ["Alice","Bob"] or [101,102]
        out = _service().assign_volunteers(
            csr_id=g.current_user["id"],
            request_id=request_id,
            volunteers=volunteers,
        )
        return jsonify(out), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400