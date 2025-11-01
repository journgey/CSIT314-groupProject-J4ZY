from flask import Blueprint, request, jsonify
from backend.services.requests_search_service import RequestsSearchService
from backend.repositories.requests_search_repository import RequestsSearchRepository
from backend.db_session import get_db

requests_search_bp = Blueprint("requests_search", __name__)

def _service():
    repo = RequestsSearchRepository(get_db())
    return RequestsSearchService(repo)

@requests_search_bp.get("/search")
def search_requests():
    """
    Search/filter requests by category, region, district, or creation date.
    Example: /requests/search?category_id=4&region_id=1&created_at=2025-11-01
    """
    service = _service()

    # Collect filters from query parameters
    filters = {
        "category_id": request.args.get("category_id", type=int),
        "region_id": request.args.get("region_id", type=int),
        "district_id": request.args.get("district_id", type=int),
        "created_at": request.args.get("created_at", type=str),
    }

    # Remove keys with None values
    filters = {k: v for k, v in filters.items() if v is not None}

    # Perform filtered search
    results = service.search_requests(filters)
    return jsonify(results), 200
