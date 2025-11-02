import re
from flask import Blueprint, request, jsonify, current_app
from backend.services.address_service import AddressService
from backend.repositories.geo_repository import GeoRepository
from backend.db_session import get_db

addresses_bp = Blueprint("addresses", __name__)
_POSTAL_RE = re.compile(r"^\d{6}$")

def _svc() -> AddressService:
    return AddressService(GeoRepository(get_db()))

@addresses_bp.post("/lookup")
def lookup():
    try:
        data = request.get_json(silent=True) or {}
    except Exception as e:
        return jsonify({"error": "Invalid JSON body"}), 400
    
    postal = (data.get("postal_code") or "").strip()
    if not postal:
        return jsonify({"error": "postal_code is required"}), 400
    if not _POSTAL_RE.match(postal):
        return jsonify({"error": "postal_code must be 6 digits (e.g., 238801)"}), 400

    try:
        res = _svc().lookup(postal)
        return jsonify(res), 200
    except ValueError as ve:
        # 예: "Postal code not found"
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        current_app.logger.exception("lookup failed")
        return jsonify({"error": "Address lookup failed"}), 500

@addresses_bp.get("/regions")
def regions():
    repo = GeoRepository(get_db())
    return jsonify(repo.list_regions()), 200

@addresses_bp.get("/districts")
def districts():
    region_id = request.args.get("region_id", type=int)
    repo = GeoRepository(get_db())
    return jsonify(repo.list_districts(region_id)), 200
