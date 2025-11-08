from flask import Blueprint, request, jsonify, g
from backend.auth import login_required, require_role
from backend.db_session import get_db
from backend.repositories.requests_repository import RequestsRepository
from backend.repositories.accounts_repository import AccountsRepository
from backend.controllers.matching_controller import MatchingController
from backend.repositories.notifications_repository import NotificationsRepository


matching_bp = Blueprint("matching", __name__)  

def _service():
    conn = get_db()
    return MatchingController(
        requests_repo=RequestsRepository(conn),
        accounts_repo=AccountsRepository(conn),
        notifications_repo=NotificationsRepository(conn),
    )

@matching_bp.put("/request/<int:request_id>/accept")
@login_required
@require_role("CSR")
def accept_and_assign(request_id: int):
    payload = request.get_json(silent=True) or {}
    volunteers = payload.get("volunteers", [])
    out = _service().accept_and_assign(
        csr_id=g.current_user["id"],
        request_id=request_id,
        volunteers=volunteers
    )
    return jsonify(out), 200