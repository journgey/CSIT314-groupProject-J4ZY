from flask import Blueprint, jsonify
from repository.db import get_conn

categories_bp = Blueprint("categories", __name__)

@categories_bp.route("/", methods=["GET"])
def list_categories_http():
    conn = get_conn()
    rows = conn.execute("SELECT id, name, description FROM categories ORDER BY id").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])
