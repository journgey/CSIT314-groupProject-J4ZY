from flask import Blueprint, request, jsonify, session, current_app
import backend.db_session as db_session
from backend.repositories.auth_repository import AuthRepository
from backend.controllers.auth_controller import AuthController

auth_bp = Blueprint("auth", __name__)

def _svc():
    get_db = current_app.config.get("GET_DB", db_session.get_db)
    return AuthController(AuthRepository(get_db()))

@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email"); password = data.get("password")
    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    try:
        user = _svc().login(email, password)
    except ValueError as e:
        return jsonify({"error": str(e)}), 401

    session["user"] = user 
    return jsonify({"ok": True, "user": user}), 200

@auth_bp.post("/logout")
def logout():
    session.pop("user", None)
    return jsonify({"ok": True}), 200

@auth_bp.get("/me")
def me():
    return jsonify(session.get("user") or {}), 200