from flask import Blueprint, request, jsonify, g
from backend.services.categories_service import CategoriesService
from backend.repositories.categories_repository import CategoriesRepository
from backend.db_session import get_db
from backend.auth import login_required, require_role

categories_bp = Blueprint("categories", __name__)

def _service():
    repo = CategoriesRepository(get_db())
    return CategoriesService(repo)

@categories_bp.post("/")
@login_required
@require_role("PlatformManager")
def create_category():
    """Create a category."""
    service = _service()
    payload = request.get_json() or {}
    try:
        created = service().create_category(payload, acting_role=g.current_user.get("role"))
        return jsonify(created), 201
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@categories_bp.get("/<int:category_id>")
@login_required
@require_role("PlatformManager")
def get_category(category_id: int):
    """Retrieve a single category by ID."""
    service = _service()
    try:
        cat = service().get_category_by_id(category_id, acting_role=g.current_user.get("role"))
        if not cat:
            return jsonify({"error": "Category not found"}), 404
        return jsonify(cat), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

@categories_bp.get("/")
@login_required
@require_role("PlatformManager")
def list_categories():
    """List all categories."""
    service = _service()
    try:
        items = service().list_categories(acting_role=g.current_user.get("role"))
        return jsonify(items), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

@categories_bp.put("/<int:category_id>")
@login_required
@require_role("PlatformManager")
def update_category(category_id: int):
    """Update a category by ID."""
    service = _service()
    payload = request.get_json() or {}
    try:
        updated = service().update_category(category_id, payload, acting_role=g.current_user.get("role"))
        if not updated:
            return jsonify({"error": "Category not found"}), 404
        return jsonify(updated), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@categories_bp.delete("/<int:category_id>")
@login_required
@require_role("PlatformManager")
def delete_category(category_id: int):
    """Delete a category by ID."""
    service = _service()
    try:
        ok = service().delete_category(category_id, acting_role=g.current_user.get("role"))
        if not ok:
            return jsonify({"error": "Category not found"}), 404
        return jsonify({"message": "Category deleted"}), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
