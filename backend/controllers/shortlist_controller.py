from flask import Blueprint, request, jsonify
from backend.db_session import get_db
from backend.repositories.shortlist_repository import ShortlistRepository
from backend.repositories.requests_repository import RequestsRepository
from backend.repositories.accounts_repository import AccountsRepository
from backend.services.shortlist_service import ShortlistService
from backend.auth import login_required, require_role

shortlists_bp = Blueprint("shortlists_bp", __name__)

def _service():
    repo = ShortlistRepository(get_db())
    req_repo = RequestsRepository(get_db())
    acc_repo = AccountsRepository(get_db())
    return ShortlistService(repo, accounts_repo=acc_repo, requests_repo=req_repo)

@login_required
@require_role("CSR")
@shortlists_bp.route("/", methods=["POST"])
def add_shortlist():
    try:
        created = _service().add_to_shortlist(request.get_json(force=True))
        return jsonify(created), (200 if created.get("duplicate") else 201)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
@login_required
@require_role("CSR")
@shortlists_bp.route("/", methods=["GET"])
def list_by_csr():
    csr_id = request.args.get("csr_id", type=int)
    if csr_id is None:
        return jsonify({"error": "csr_id is required"}), 400
    items = _service().list_shortlist(csr_id)
    return jsonify({"items": items}), 200

@login_required
@require_role("CSR")
@shortlists_bp.route("/<int:shortlist_id>", methods=["DELETE"])
def remove_shortlist(shortlist_id: int):
    try:
        result = _service().remove_shortlist(shortlist_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@login_required
@require_role("CSR")
@shortlists_bp.route("/", methods=["DELETE"])
def delete_by_pair():
    csr_id = request.args.get("csr_id", type=int)
    req_id = request.args.get("request_id", type=int)
    if csr_id is None or req_id is None:
        return jsonify({"error": "csr_id and request_id must be provided"}), 400
    try:
        result = _service().remove_shortlist_by_pair(csr_id=csr_id, request_id=req_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404