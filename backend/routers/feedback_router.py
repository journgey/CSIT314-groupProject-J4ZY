from flask import Blueprint, request, jsonify, g
from backend.db_session import get_db
from backend.repositories.feedback_repository import FeedbackRepository
from backend.controllers.feedback_controller import FeedbackController
from backend.auth import login_required, require_role

feedback_bp = Blueprint("feedbacks_bp", __name__)

def _service() -> FeedbackController:
    conn = get_db()
    repo = FeedbackRepository(conn)
    return FeedbackController(repo)

@feedback_bp.route("/", methods=["POST"])
@login_required
@require_role("PIN")
def create_feedback():
    payload = request.get_json(force=True) or {}
    request_id = payload.get("request_id")
    comment = payload.get("comment")
    rating = payload.get("rating")
    if not isinstance(request_id, int):
        return jsonify({"error": "request_id must be an integer"}), 400
    if not isinstance(rating, int):
        return jsonify({"error": "rating must be an integer"}), 400

    result = _service().create_feedback(
        request_id=request_id,
        pin_id=g.current_user["id"],
        comment=comment,
        rating=rating,
    )
    return jsonify(result), 201


@feedback_bp.route("/request/<int:request_id>", methods=["GET"])
@login_required
@require_role("PIN", "CSR")
def get_feedback_for_request(request_id: int):
    result = _service().get_feedback_for_request_authorized(
        request_id=request_id,
        user_id=g.current_user["id"],
        role=g.current_user.get("role"),
    )
    return jsonify(result), 200


@feedback_bp.route("/csr/history", methods=["GET"])
@login_required
@require_role("CSR")
def list_feedback_for_csr():
    items = _service().list_feedback_for_csr(csr_id=g.current_user["id"])
    return jsonify({"items": items}), 200