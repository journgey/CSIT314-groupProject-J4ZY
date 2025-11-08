from typing import Dict, Any
from datetime import datetime
from backend.repositories.requests_search_repository import RequestsSearchRepository

_DATE_FMT = "%Y-%m-%d"
_ALLOWED_SORT = {"id", "created_at", "start_at", "end_at"} 
_ALLOWED_ORDER = {"asc", "desc"}
_ALLOWED_STATUS = {"pending","shortlisted","accepted","completed","expired"}

def _parse_date(field: str, value: str):
    try:
        return datetime.strptime(value, _DATE_FMT).date()
    except ValueError:
        raise ValueError(f"{field} must follow YYYY-MM-DD format")
    
def _split_status(value):
    if value is None:
        return None
    items = [s.strip().lower() for s in str(value).split(",") if s.strip()]
    if not items:
        return None
    bad = [s for s in items if s not in _ALLOWED_STATUS]
    if bad:
        raise ValueError(f"status must be CSV of {_ALLOWED_STATUS}, got {bad}")
    return items

class RequestsSearchController:
    def __init__(self, repository: RequestsSearchRepository):
        self.repository = repository

    def _normalize_common(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        norm: Dict[str, Any] = dict(filters or {})
        
        limit = norm.get("limit", 20); offset = norm.get("offset", 0)
        if not isinstance(limit, int) or limit <= 0 or limit > 200:
            raise ValueError("limit must be a positive integer <= 200")
        if not isinstance(offset, int) or offset < 0:
            raise ValueError("offset must be a non-negative integer")
        norm["limit"], norm["offset"] = limit, offset
        
        sort = str(norm.get("sort", "end_at")); order = str(norm.get("order", "desc")).lower()
        if sort not in _ALLOWED_SORT: raise ValueError(f"sort must be one of {sorted(_ALLOWED_SORT)}")
        if order not in _ALLOWED_ORDER: raise ValueError("order must be 'asc' or 'desc'")
        norm["sort"], norm["order"] = sort, order
        
        for key in ("date_from","date_to"):
            if key in norm and norm[key] is not None:
                norm[key] = _parse_date(key, norm[key])
        
        for k in ("category_id",):
            if k in norm and norm[k] is not None and not isinstance(norm[k], int):
                raise ValueError(f"{k} must be an integer")
        norm["only_with_feedback"] = bool(norm.get("only_with_feedback", False))
        return norm

    def search_requests(self, filters: Dict[str, Any]):
        norm: Dict[str, Any] = dict(filters or {})

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

        sort = str(norm.get("sort", "created_at"))
        order = str(norm.get("order", "desc")).lower()
        if sort not in _ALLOWED_SORT:
            raise ValueError(f"sort must be one of {sorted(_ALLOWED_SORT)}")
        if order not in _ALLOWED_ORDER:
            raise ValueError("order must be 'asc' or 'desc'")
        norm["sort"] = sort
        norm["order"] = order

        if "created_at" in norm and norm["created_at"] is not None:
            _parse_date("created_at", norm["created_at"])

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

        for int_key in ("category_id", "region_id", "district_id"):
            if int_key in norm and norm[int_key] is not None and not isinstance(norm[int_key], int):
                raise ValueError(f"{int_key} must be an integer")
            
        norm["status_list"] = _split_status(norm.pop("status", None))

        for k in ("pin_id","csr_id"):
            if k in norm and norm[k] is not None and not isinstance(norm[k], int):
                raise ValueError(f"{k} must be an integer")

        return self.repository.search_requests(norm)
    
    def search_pin_history(self, pin_id: int, filters: Dict[str, Any]):
        norm = self._normalize_common(filters)
        norm.update({
            "pin_id": pin_id,
            "history_scope": "pin",
        })
        return self.repository.search_history(norm)

    def search_csr_history(self, csr_id: int, filters: Dict[str, Any]):
        norm = self._normalize_common(filters)
        norm.update({
            "csr_id": csr_id,
            "history_scope": "csr",
        })
        return self.repository.search_history(norm)