from flask import Blueprint, request, jsonify
from services.accounts_service import AccountService
from repositories.accounts_repository import AccountsRepository
from db_session import get_db

# Blueprint for accounts endpoints
accounts_bp = Blueprint("accounts", __name__)

def _service():
    repo = AccountsRepository(get_db())
    return AccountService(repo)

# Create account
@accounts_bp.post("/")
def create_account():
    service = _service()
    data = request.get_json()
    created = service.create_account(data)
    return jsonify(created), 201

# Get single account by ID
@accounts_bp.get("/<int:account_id>")
def get_account(account_id: int):
    service = _service()
    account = service.get_account_by_id(account_id)
    if not account:
        # Return 404 when repository has no such record
        return jsonify({"error": "Account not found"}), 404
    return jsonify(account), 200

# List all accounts
@accounts_bp.get("/")
def list_accounts():
    service = _service()
    accounts = service.list_accounts()
    return jsonify(accounts), 200

# Update account
@accounts_bp.put("/<int:account_id>")
def update_account(account_id: int):
    service = _service()
    data = request.get_json() or {}
    updated = service.update_account(account_id, data)
    if not updated:
        return jsonify({"error": "Account not found"}), 404
    return jsonify(updated), 200

# Delete account
@accounts_bp.delete("/<int:account_id>")
def delete_account(account_id):
    service = _service()
    success = service.delete_account(account_id)
    if not success:
        return jsonify({"error": "Account not found"}), 404
    return jsonify({"message": "Account deleted"}), 200

# Search account
@accounts_bp.get("/search")
def search_accounts():
    service = _service()
    """
    Simple search:
      - GET /api/accounts/search?email=foo@example.com
      - GET /api/accounts/search?name=Ali&partial=true
    """
    email = request.args.get("email")
    name = request.args.get("name")
    partial = request.args.get("partial", "true").lower() == "true"  # default: substring match

    # Disallow ambiguous queries
    if email and name:
        return jsonify({"error": "Use either 'email' or 'name'"}), 400

    if email:
        acc = service.get_account_by_email(email)
        return (jsonify(acc), 200) if acc else (jsonify({"error": "Account not found"}), 404)

    if name:
        results = service.search_accounts_by_name(name=name, partial=partial)
        return jsonify(results), 200

    return jsonify({"error": "Provide 'email' or 'name'"}), 400