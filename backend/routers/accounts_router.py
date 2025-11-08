from flask import Blueprint, current_app, request, jsonify, g
from backend.controllers.accounts_controller import AccountController
from backend.repositories.accounts_repository import AccountsRepository
from backend.db_session import get_db
from backend.auth import login_required, require_role

accounts_bp = Blueprint("accounts", __name__)

def _service():
    repo = AccountsRepository(get_db())
    return AccountController(repo)

@accounts_bp.post("/")
def create_account():
    service = _service()
    data = request.get_json()
    created = service.create_account(data)
    return jsonify(created), 201

@accounts_bp.get("/<int:account_id>")
@login_required
@require_role("UserAdmin")
def get_account(account_id: int):
    service = _service()
    account = service.get_account_by_id(account_id, acting_role=g.current_user.get("role"))
    if not account:
        return jsonify({"error": "Account not found"}), 404
    return jsonify(account), 200

@accounts_bp.get("/")
@login_required
@require_role("UserAdmin")
def list_accounts():
    service = _service()
    accounts = service.list_accounts(acting_role=g.current_user.get("role"))
    return jsonify(accounts), 200

@accounts_bp.put("/<int:account_id>")
@login_required
@require_role("UserAdmin")
def update_account(account_id: int):
    service = _service()
    data = request.get_json() or {}
    updated = service.update_account(account_id, data, acting_role=g.current_user.get("role"))
    if not updated:
        return jsonify({"error": "Account not found"}), 404
    return jsonify(updated), 200

@accounts_bp.delete("/<int:account_id>")
@login_required
@require_role("UserAdmin")
def delete_account(account_id):
    service = _service()
    success = service.delete_account(account_id, acting_role=g.current_user.get("role"))
    if not success:
        return jsonify({"error": "Account not found"}), 404
    return jsonify({"message": "Account deleted"}), 200