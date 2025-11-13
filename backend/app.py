from __future__ import annotations
import sys
import sqlite3
from pathlib import Path
from flask import Flask, jsonify, g, render_template, send_from_directory
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

from backend.auth import require_role
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
    app = Flask(__name__,
        static_folder=str(PROJECT_ROOT / "frontend" / "static"),      
        template_folder=str(PROJECT_ROOT / "frontend" / "templates"), 
    )

    # 1) Config
    app.config.update(
        SECRET_KEY="dev-secret-key",     
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
    from backend.routers import (
    auth_router, accounts_router, categories_router, requests_router,
    feedback_router, notifications_router,
    reports_router, shortlist_router, matching_router,
    requests_search_router, address_router, volunteers_router
    )

    bps = [
        (auth_router.auth_bp, "/api/auth"),
        (accounts_router.accounts_bp, "/api/account"),
        (categories_router.categories_bp, "/api/category"),
        (requests_router.requests_bp, "/api/request"),
        (feedback_router.feedback_bp, "/api/feedback"),
        (notifications_router.notifications_bp, "/api/notification"),
        (reports_router.reports_bp, "/api/report"),
        (shortlist_router.shortlists_bp, "/api/shortlist"),
        (matching_router.matching_bp, "/api"),
        (requests_search_router.requests_search_bp, "/api/request"),
        (address_router.addresses_bp, "/api/address"),
        (volunteers_router.volunteers_bp, "/api/volunteer"),
    ]

    for bp, prefix in bps:
        app.register_blueprint(bp, url_prefix=prefix)

    @app.get("/")
    def index():
        return render_template("index.html")
    
    @app.get("/create_account")
    def user_new():
        return render_template("create_account.html")
    
    @app.get("/useradmin")
    @require_role("UserAdmin")
    def useradmin_dashboard():
        return render_template("UA_accounts.html")

    @app.get("/pm")
    @require_role("PlatformManager")
    def pm_dashboard():
        return render_template("PM_requests.html")

    @app.get("/pin")
    def pin_dashboard():
        return render_template("PIN_mypage.html")

    @app.get("/csr")
    def csr_dashboard():
        return render_template("CSR_mypage.html")
    
    @app.get("/pm/view_request")
    @require_role("PlatformManager")
    def PM_view_request():
        return send_from_directory(app.template_folder, "PM_view_request.html")
    
    @app.get("/pm/gen_report")
    @require_role("PlatformManager")
    def PM_gen_report():
        return send_from_directory(app.template_folder, "PM_gen_report.html")
    
    @app.get("/pm/categories")
    @require_role("PlatformManager")
    def PM_categories():
        return send_from_directory(app.template_folder, "PM_categories.html")
    
    @app.get("/ua/edit_account")
    @require_role("UserAdmin")
    def UA_edit_account():
        return render_template("UA_edit_account.html")
    
    @app.get("/pin/view_request")
    @require_role("PIN")
    def PIN_view_request():
        return render_template("PIN_view_request.html")
    
    @app.get("/pin/edit_request")
    @require_role("PIN")
    def PIN_edit_request():
        return render_template("PIN_edit_request.html")
    
    @app.get("/pin/history")
    def PIN_history():
        return render_template("PIN_history.html")
    
    @app.get("/pin/feedback")
    @require_role("PIN")
    def PIN_create_feedback():
        return render_template("PIN_create_feedback.html")
    
    @app.get("/csr/all_requests")
    def CSR_view_all_pending_requests():
        return render_template("CSR_view_all_pending_requests.html")
    
    @app.get("/csr/view_request")
    @require_role("CSR")
    def CSR_view_request():
        return render_template("CSR_view_request.html")
    
    @app.get("/csr/history")
    @require_role("CSR")
    def CSR_history():
        return render_template("CSR_history.html")
    
    @app.get("/csr/match")
    @require_role("CSR")
    def CSR_create_matching():
        return render_template("CSR_create_matching.html")
    
    @app.get("/csr/volunteers")
    @require_role("CSR")
    def CSR_manage_volunteers():
        return render_template("CSR_manage_volunteers.html")

    # 6) Global error handlers
    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        return jsonify({"error": e.errors()}), 400

    @app.errorhandler(ValueError)
    def handle_value_error(e):
        return jsonify({"error": str(e)}), 400
    
    @app.errorhandler(PermissionError)
    def handle_perm(e):
        return jsonify({"error": str(e)}), 403

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
