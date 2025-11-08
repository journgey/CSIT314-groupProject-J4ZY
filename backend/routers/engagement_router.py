from flask import Blueprint, jsonify, g
from backend.db_session import get_db
from backend.repositories.engagement_repository import EngagementsRepository
from backend.controllers.engagement_controller import EngagementsController
from backend.auth import login_required, require_role

engagements_bp = Blueprint("engagements_bp", __name__)

def _service() -> EngagementsController:
    repo = EngagementsRepository(get_db())
    return EngagementsController(repo)

@engagements_bp.route("/", methods=["GET"])
@login_required
@require_role("PIN")
def list_engagement():
    try:
        pin_id = g.current_user["id"]
        items = _service().list_pin_engagement(pin_id)
        return jsonify({"items": items}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
