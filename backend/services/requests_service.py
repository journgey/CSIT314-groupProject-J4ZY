from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from backend.schemas.requests import Request  # Pydantic schema with business validators

class RequestsService:
    """Business logic for requests."""

    def __init__(self, repository): 
        self.repository = repository


    @staticmethod
    def _serialize_volunteers(vols):
        """Ensure volunteers are a list[int] for persistence (repo may store JSON)."""
        if vols is None:
            return []
        if isinstance(vols, list):
            return vols
        # Accept comma-separated strings as a fallback
        if isinstance(vols, str) and vols.strip():
            return [int(x) for x in vols.split(",") if x.strip().isdigit()]
        return []


    def create_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and create a request, returning the created row."""
        # Normalize volunteers before schema validation
        data = dict(payload)
        data["volunteers"] = self._serialize_volunteers(payload.get("volunteers"))

        # Validate against Pydantic schema (status/CSR/volunteers constraints, dates, etc.)
        req = Request(**data)

        created = self.repository.create_request(
            pin_id=req.pin_id,
            csr_id=req.csr_id,
            category_id=req.category_id,
            district_id=req.district_id,
            title=req.title,
            description=req.description,
            status=req.status.value if hasattr(req.status, "value") else req.status,  # enum-safe
            start_at=req.start_at,
            end_at=req.end_at,
            created_at=req.created_at or datetime.utcnow(),
            volunteers=json.dumps(req.volunteers or []),  # store as JSON text
        )

        # Return fresh row for consistent shape
        fresh = self.repository.get_request_by_id(created["id"])
        return fresh or created

    def get_request_by_id(self, req_id: int) -> Optional[Dict[str, Any]]:
        row = self.repository.get_request_by_id(req_id)
        return row

    def list_requests(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        rows = self.repository.list_requests(filters or {})
        return rows

    def update_request(self, req_id: int, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        current = self.repository.get_request_by_id(req_id)
        if not current:
            return None

        data = dict(payload)
        if "volunteers" in data:
            data["volunteers"] = self._serialize_volunteers(data.get("volunteers"))

        # Merge → re-validate to enforce invariants from schema
        merged = {**current, **data}
        # Convert volunteers TEXT->list if repository returned JSON string
        if isinstance(merged.get("volunteers"), str):
            try:
                merged["volunteers"] = json.loads(merged["volunteers"])
            except Exception:
                merged["volunteers"] = []
        Request(**merged)  # validation only

        # Persist
        self.repository.update_request(req_id, **data)

        # Return updated row
        return self.repository.get_request_by_id(req_id)

    def delete_request(self, req_id: int) -> bool:
        try:
            self.repository.delete_request(req_id)
            return True
        except ValueError:
            return False
