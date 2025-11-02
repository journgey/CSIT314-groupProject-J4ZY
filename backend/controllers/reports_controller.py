from flask import Blueprint, request, jsonify
from backend.db_session import get_db
from backend.repositories.reports_repository import ReportsRepository
from backend.services.reports_service import ReportsService
from backend.auth import login_required, require_role

reports_bp = Blueprint("reports_bp", __name__)

def _service() -> ReportsService:
    """
    Factory: inject DB connection and wire Repo -> Service.
    """
    conn = get_db()
    repo = ReportsRepository(conn)
    return ReportsService(repo)

@reports_bp.route("/", methods=["GET"])
@login_required
@require_role("PlatformManager")
def generate_report():
    """
    Build the report for a given date range.
    Query params:
      - start: YYYY-MM-DD (or full timestamp)
      - end  : YYYY-MM-DD (or full timestamp)
    Returns:
      {
        meta: {...},
        created_status: [{status, count}],
        ended_performance: {ended_total, matched_count, completed_count, expired_count},
        regional: { created: [...], ended: [...] },
        category: { created: [...], ended: [...] }
      }
    """
    start = request.args.get("start")
    end = request.args.get("end")
    if not start or not end:
        return jsonify({"error": "start and end are required"}), 400

    try:
        payload = _service().build_report(start, end)
        return jsonify(payload), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception:
        # Fallback error to avoid leaking details
        return jsonify({"error": "Internal server error"}), 500
