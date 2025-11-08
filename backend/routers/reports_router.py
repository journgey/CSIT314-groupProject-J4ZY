from flask import Blueprint, request, jsonify
from backend.db_session import get_db
from backend.repositories.reports_repository import ReportsRepository
from backend.controllers.reports_controller import ReportsController
from backend.auth import login_required, require_role

reports_bp = Blueprint("reports_bp", __name__)

def _service() -> ReportsController:
    conn = get_db()
    repo = ReportsRepository(conn)
    return ReportsController(repo)

@reports_bp.route("/", methods=["GET"])
@login_required
@require_role("PlatformManager")
def generate_report():
    start = request.args.get("start")
    end = request.args.get("end")
    if not start or not end:
        return jsonify({"error": "start and end are required"}), 400
    payload = _service().build_report(start, end)
    return jsonify(payload), 200
