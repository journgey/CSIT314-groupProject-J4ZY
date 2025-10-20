from flask import Blueprint, request, jsonify

categories_bp = Blueprint("categories", __name__, url_prefix="/categories")

@categories_bp.post("/")
def create_category():
    pass

@categories_bp.get("/<category_id>")
def get_category(category_id):
    pass

@categories_bp.get("/")
def list_categories():
    pass

@categories_bp.put("/<category_id>")
def update_category(category_id):
    pass

@categories_bp.delete("/<category_id>")
def delete_category(category_id):
    pass