from flask import Blueprint, request, jsonify
from repositories.categories_repository import CategoriesRepository
from services.categories_service import CategoriesService
from db_session import get_db

categories_bp = Blueprint("categories", __name__)

def _service():
    repo = CategoriesRepository(get_db())
    return CategoriesService(repo)

@categories_bp.post("/")
def create_category():
    """Create a category."""
    service = _service()
    payload = request.get_json() or {}
    created = service.create_category(payload)
    return jsonify(created), 201

@categories_bp.get("/<int:category_id>")
def get_category(category_id: int):
    """Retrieve a single category by ID."""
    service = _service()
    cat = service.get_category_by_id(category_id)
    if not cat:
        return jsonify({"error": "Category not found"}), 404
    return jsonify(cat), 200

@categories_bp.get("/")
def list_categories():
    """List all categories."""
    service = _service()
    items = service.list_categories()
    return jsonify(items), 200

@categories_bp.put("/<int:category_id>")
def update_category(category_id: int):
    """Update a category by ID."""
    service = _service()
    payload = request.get_json() or {}
    updated = service.update_category(category_id, payload)
    if not updated:
        return jsonify({"error": "Category not found"}), 404
    return jsonify(updated), 200

@categories_bp.delete("/<int:category_id>")
def delete_category(category_id: int):
    """Delete a category by ID."""
    service = _service()
    ok = service.delete_category(category_id)
    if not ok:
        return jsonify({"error": "Category not found"}), 404
    return jsonify({"message": "Category deleted"}), 200
