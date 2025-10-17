from flask import Blueprint, jsonify, request
from services.requests_service import (
    list_requests, get_request, create_request, update_request, delete_request
)

requests_bp = Blueprint("requests", __name__)

@requests_bp.route("/", methods=["GET"])
def http_list_requests():
    return jsonify(list_requests())

@requests_bp.route("/<int:req_id>", methods=["GET"])
def http_get_request(req_id: int):
    data = get_request(req_id)
    if not data:
        return jsonify({"error": "not found"}), 404
    return jsonify(data)

@requests_bp.route("/", methods=["POST"])
def http_create_request():
    dto = request.get_json() or {}
    try:
        data = create_request(dto)
        return jsonify(data), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@requests_bp.route("/<int:req_id>", methods=["PATCH"])
def http_update_request(req_id: int):
    dto = request.get_json() or {}
    try:
        data = update_request(req_id, dto)
        return jsonify(data)
    except KeyError:
        return jsonify({"error": "not found"}), 404

@requests_bp.route("/<int:req_id>", methods=["DELETE"])
def http_delete_request(req_id: int):
    ok = delete_request(req_id)
    return (jsonify({"deleted": True}), 200) if ok else (jsonify({"error":"not found"}), 404)
