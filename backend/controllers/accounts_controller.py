from flask import Blueprint, jsonify
from repository.db import get_conn

accounts_bp = Blueprint("accounts", __name__)

@accounts_bp.route("/", methods=["GET"])
def list_accounts_http():
    conn = get_conn()
    rows = conn.execute("SELECT id, email, name, role FROM accounts ORDER BY id").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])
