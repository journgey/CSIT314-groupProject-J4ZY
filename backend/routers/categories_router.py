from flask import Blueprint, request, jsonify, g
from backend.controllers.categories_controller import CategoriesController
from backend.repositories.categories_repository import CategoriesRepository
from backend.db_session import get_db
from backend.auth import login_required, require_role

categories_bp = Blueprint("categories", __name__)

def _service():
    repo = CategoriesRepository(get_db())
    return CategoriesController(repo)

@categories_bp.post("/")
@login_required
@require_role("PlatformManager")
def create_category():
    service = _service()
    payload = request.get_json() or {}
    created = service.create_category(payload, acting_role=g.current_user.get("role"))
    return jsonify(created), 201

@categories_bp.get("/<int:category_id>")
@login_required
@require_role("PlatformManager")
def get_category(category_id: int):
    service = _service()
    cat = service.get_category_by_id(category_id, acting_role=g.current_user.get("role"))
    if not cat:
        return jsonify({"error": "Category not found"}), 404
    return jsonify(cat), 200

@categories_bp.get("/")
@login_required
def list_categories():
    service = _service()
    include_inactive = request.args.get("include_inactive") == "true"
    items = service.list_categories(include_inactive)
    return jsonify(items), 200

@categories_bp.put("/<int:category_id>")
@login_required
@require_role("PlatformManager")
def update_category(category_id: int):
    service = _service()
    payload = request.get_json() or {}
    updated = service.update_category(category_id, payload, acting_role=g.current_user.get("role"))
    if not updated:
        return jsonify({"error": "Category not found"}), 404
    return jsonify(updated), 200

@categories_bp.delete("/<int:category_id>")
@login_required
@require_role("PlatformManager")
def deactivate_category(category_id: int):
    """Deactivate instead of hard delete"""
    service = _service()
    ok = service.deactivate_category(category_id, acting_role=g.current_user.get("role"))
    if not ok:
        return jsonify({"error": "Category not found"}), 404
    return jsonify({"message": "Category deactivated"}), 200
