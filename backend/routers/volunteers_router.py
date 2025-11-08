from flask import Blueprint, request, jsonify, g
from backend.auth import login_required, require_role
from backend.db_session import get_db
from backend.controllers.volunteers_controller import VolunteersController
from backend.repositories.volunteers_repository import VolunteersRepository

volunteers_bp = Blueprint("volunteers", __name__)

def _svc():
    return VolunteersController(VolunteersRepository(get_db()))

# ------- List -------
@volunteers_bp.get("/")
@login_required
@require_role("CSR")
def list_volunteers():
    company_id = request.args.get("company_id", type=int)
    if company_id is None:
        return jsonify({"error":"company_id is required"}), 400
    # enforce same-company
    if g.current_user.get("company_id") != company_id:
        return jsonify({"error":"forbidden"}), 403
    q = request.args.get("q")
    items = _svc().list(company_id=company_id, q=q)
    return jsonify({"items": items}), 200

# ------- Get by id -------
@volunteers_bp.get("/<int:vol_id>")
@login_required
@require_role("CSR")
def get_volunteer(vol_id: int):
    company_id = g.current_user.get("company_id")
    if company_id is None:
        return jsonify({"error":"forbidden"}), 403
    out = _svc().get(company_id=company_id, vol_id=vol_id)
    if not out:
        return jsonify({"error":"not found"}), 404
    return jsonify(out), 200

# ------- Create -------
@volunteers_bp.post("/")
@login_required
@require_role("CSR")
def create_volunteer():
    company_id = g.current_user.get("company_id")
    if company_id is None:
        return jsonify({"error":"forbidden"}), 403

    data = request.get_json(silent=True) or {}
    name  = data.get("name")
    email = data.get("email")
    phone = data.get("phone")

    out, code = _svc().create(company_id=company_id, name=name, email=email, phone=phone)
    return jsonify(out), code

# ------- Update -------
@volunteers_bp.put("/<int:vol_id>")
@login_required
@require_role("CSR")
def update_volunteer(vol_id: int):
    company_id = g.current_user.get("company_id")
    if company_id is None:
        return jsonify({"error":"forbidden"}), 403

    data = request.get_json(silent=True) or {}
    name  = data.get("name")
    email = data.get("email")
    phone = data.get("phone")

    out, code = _svc().update(company_id=company_id, vol_id=vol_id, name=name, email=email, phone=phone)
    return jsonify(out), code

# ------- Delete -------
@volunteers_bp.delete("/<int:vol_id>")
@login_required
@require_role("CSR")
def delete_volunteer(vol_id: int):
    company_id = g.current_user.get("company_id")
    if company_id is None:
        return jsonify({"error":"forbidden"}), 403
    out, code = _svc().delete(company_id=company_id, vol_id=vol_id)
    return jsonify(out), code
