from flask import Blueprint, request, jsonify

requests_bp = Blueprint("requests", __name__, url_prefix="/requests")

@requests_bp.post("/")
def create_request():
    pass

@requests_bp.get("/<request_id>")
def get_request(request_id):
    pass

@requests_bp.get("/")
def list_requests():
    pass

@requests_bp.put("/<request_id>")
def update_request(request_id):
    pass

@requests_bp.delete("/<request_id>")
def delete_request(request_id):
    pass