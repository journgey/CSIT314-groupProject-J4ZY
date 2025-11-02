from typing import Dict, Any
from datetime import datetime
from backend.repositories.requests_search_repository import RequestsSearchRepository

_DATE_FMT = "%Y-%m-%d"
_ALLOWED_SORT = {"id", "created_at", "start_at", "end_at"}  # modify if schema has more fields
_ALLOWED_ORDER = {"asc", "desc"}

def _parse_date(field: str, value: str):
    try:
        return datetime.strptime(value, _DATE_FMT).date()
    except ValueError:
        raise ValueError(f"{field} must follow YYYY-MM-DD format")

class RequestsSearchService:
    def __init__(self, repository: RequestsSearchRepository):
        self.repository = repository

    def search_requests(self, filters: Dict[str, Any]):
        """
        - Validate and normalize all incoming filters.
        - If validation fails, raise ValueError (handled globally as HTTP 400).
        """
        norm: Dict[str, Any] = dict(filters or {})

        # 1) Pagination validation
        limit = norm.get("limit", 20)
        offset = norm.get("offset", 0)
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError("limit must be a positive integer")
        if limit > 200:
            raise ValueError("limit must be <= 200")
        if not isinstance(offset, int) or offset < 0:
            raise ValueError("offset must be a non-negative integer")
        norm["limit"] = limit
        norm["offset"] = offset

        # 2) Sorting validation
        sort = str(norm.get("sort", "created_at"))
        order = str(norm.get("order", "desc")).lower()
        if sort not in _ALLOWED_SORT:
            raise ValueError(f"sort must be one of {sorted(_ALLOWED_SORT)}")
        if order not in _ALLOWED_ORDER:
            raise ValueError("order must be 'asc' or 'desc'")
        norm["sort"] = sort
        norm["order"] = order

        # 3) Date validation (if provided)
        # created_at: specific date filter (may be handled as = or range in repository)
        if "created_at" in norm and norm["created_at"] is not None:
            _parse_date("created_at", norm["created_at"])

        # start_at / end_at: validate format and logical order
        if "start_at" in norm and norm["start_at"] is not None:
            start_d = _parse_date("start_at", norm["start_at"])
        else:
            start_d = None

        if "end_at" in norm and norm["end_at"] is not None:
            end_d = _parse_date("end_at", norm["end_at"])
        else:
            end_d = None

        if start_d and end_d and start_d > end_d:
            raise ValueError("start_at must be earlier than or equal to end_at")

        # 4) Numeric fields validation (redundant but ensures data safety)
        for int_key in ("category_id", "region_id", "district_id"):
            if int_key in norm and norm[int_key] is not None and not isinstance(norm[int_key], int):
                raise ValueError(f"{int_key} must be an integer")

        # Pass normalized filters to repository
        return self.repository.search_requests(norm)