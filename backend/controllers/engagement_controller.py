from flask import Blueprint, jsonify, g
from backend.db_session import get_db
from backend.repositories.engagement_repository import EngagementsRepository
from backend.services.engagement_service import EngagementsService
from backend.auth import login_required, require_role

engagements_bp = Blueprint("engagements_bp", __name__)

def _service() -> EngagementsService:
    """
    Factory for injecting dependencies:
    - get_db() -> EngagementsRepository -> EngagementsService
    """
    repo = EngagementsRepository(get_db())
    return EngagementsService(repo)

@engagements_bp.route("/", methods=["GET"])
@login_required
@require_role("PIN")
def list_engagement():
    """
    Return engagement metrics for the currently logged-in PIN.
    - Status is computed by the DB (no application-side status updates).
    - Only requests with computed_status in ('pending','accepted') and not past end_at are included.
    """
    try:
        pin_id = g.current_user["id"]
        items = _service().list_pin_engagement(pin_id)
        return jsonify({"items": items}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
