from flask import Blueprint, request, jsonify

accounts_bp = Blueprint("accounts", __name__, url_prefix="/accounts")

@accounts_bp.post("/")
def create_account():
    pass

@accounts_bp.get("/<account_id>")
def get_account(account_id):
    pass

@accounts_bp.get("/")
def list_accounts():
    pass

@accounts_bp.put("/<account_id>")
def update_account(account_id):
    pass

@accounts_bp.delete("/<account_id>")
def delete_account(account_id):
    pass