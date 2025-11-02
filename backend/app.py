from __future__ import annotations
import sys
import sqlite3
from pathlib import Path
from flask import Flask, jsonify, g
from flask_cors import CORS
from pydantic import ValidationError
from datetime import timedelta

# -----------------------------
# Paths & import wiring
# -----------------------------
BACKEND_DIR = Path(__file__).resolve().parent          # .../gp/backend
PROJECT_ROOT = BACKEND_DIR.parent                      # .../gp
SEED_DIR = PROJECT_ROOT / "seed"
DB_SQL = BACKEND_DIR / "db.sql"
DB_PATH = BACKEND_DIR / "surething.db"                 # DB file next to app.py
DATA_DIR = PROJECT_ROOT / "data"

# Make project & seed importable no matter where we run from
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if SEED_DIR.exists() and str(SEED_DIR) not in sys.path:
    sys.path.insert(0, str(SEED_DIR))

from seed import import_from_json as seeder  # after sys.path wiring
from backend.db_session import close_db

# -----------------------------
# One-shot helpers (schema & seed)
# -----------------------------
def _apply_schema_idempotent(conn, sql_text: str):
    """Apply schema; ignore 'already exists' errors to be idempotent."""
    cur = conn.cursor()
    try:
        cur.executescript(sql_text)
    except sqlite3.OperationalError as e:
        raise
    finally:
        conn.commit()

def _ensure_schema_then_seed():
    """Create/upgrade schema and seed using a single one-off connection."""
    BACKEND_DIR.mkdir(parents=True, exist_ok=True)
    # One-off connection (not request-scoped)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    # 1) Schema
    with open(DB_SQL, "r", encoding="utf-8") as f:
        _apply_schema_idempotent(conn, f.read())

    # 2) Seed (use same connection to avoid 'no such table')
    seeder.run_with_existing_conn(conn, SEED_DIR)

    conn.close()

# -----------------------------
# Flask factory
# -----------------------------
def create_app():
    app = Flask(__name__)

    # 1) Config
    app.config.update(
        SECRET_KEY="dev-secret-key",      # 코드 안에 하드코딩
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=False,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        SESSION_PERMANENT=True,
    )

    # 2) Extensions: CORS for all /api/* endpoints (adjust as needed)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # 3) Boot: schema → seed (safe to call at every start)
    _ensure_schema_then_seed()

    # 4) Close DB per request/app context
    app.teardown_appcontext(close_db)

    # 5) Register blueprints (blueprints must not set their own url_prefix)
    from backend.controllers.auth_controller import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    from backend.controllers.accounts_controller import accounts_bp
    app.register_blueprint(accounts_bp, url_prefix="/api/accounts")

    from backend.controllers.categories_controller import categories_bp
    app.register_blueprint(categories_bp, url_prefix="/api/categories")

    from backend.controllers.requests_controller import requests_bp
    app.register_blueprint(requests_bp, url_prefix="/api/requests")

    from backend.controllers.engagement_controller import engagements_bp
    app.register_blueprint(engagements_bp, url_prefix="/api/engagements")

    from backend.controllers.feedback_controller import feedback_bp
    app.register_blueprint(feedback_bp, url_prefix="/api/feedbacks")

    from backend.controllers.notifications_controller import notifications_bp
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")

    from backend.controllers.reports_controller import reports_bp
    app.register_blueprint(reports_bp, url_prefix="/api/reports")

    from backend.controllers.shortlist_controller import shortlists_bp
    app.register_blueprint(shortlists_bp, url_prefix="/api/shortlists")

    from backend.controllers.matching_controller import matching_bp
    app.register_blueprint(matching_bp, url_prefix="/api")

    from backend.controllers.requests_search_controller import requests_search_bp
    app.register_blueprint(requests_search_bp, url_prefix="/api/requests")


    # 6) Global error handlers
    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        return jsonify({"error": e.errors()}), 400

    @app.errorhandler(ValueError)
    def handle_value_error(e):
        return jsonify({"error": str(e)}), 400

    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def handle_internal_error(e):
        return jsonify({"error": "Internal server error"}), 500

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
