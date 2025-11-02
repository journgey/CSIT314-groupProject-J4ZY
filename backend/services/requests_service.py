from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from backend.db_session import get_db
from backend.repositories.geo_repository import GeoRepository
from backend.services.address_service import AddressService

class RequestsService:
    """
    Business rules:
    - PIN: create; update/delete only own requests
    - PlatformManager: delete any request
    - CSR: read only (accept is handled in matching module)
    - Status is computed in DB (v_requests_status), never stored.
    """

    def __init__(self, repository):
        self.repository = repository

    # -------------- utils --------------
    @staticmethod
    def _serialize_volunteers(vols):
        if vols is None:
            return []
        if isinstance(vols, list):
            return vols
        if isinstance(vols, str) and vols.strip():
            return [int(x) for x in vols.split(",") if x.strip().isdigit()]
        return []

    # -------------- read --------------
    def get_request_by_id(self, req_id: int) -> Optional[Dict[str, Any]]:
        item = self.repository.get_request_by_id(req_id)
        if item:
            self.repository.increment_view_count(req_id)
        return self.repository.get_request_by_id(req_id)

    def list_requests(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return self.repository.list_requests(filters or {})

    # -------------- create (PIN only) --------------
    def create_request(self, payload: Dict[str, Any], *, acting_user_id: int, acting_role: str) -> Dict[str, Any]:
        if acting_role != "PIN":
            raise PermissionError("Only PIN can create requests")

        # Address enrichment (district/region inference etc.)
        payload = AddressService(GeoRepository(get_db())).enrich_request_payload(payload)

        data = dict(payload)
        # Force ownership to current PIN
        provided_pin_id = data.get("pin_id")
        if provided_pin_id is None:
            data["pin_id"] = acting_user_id
        elif provided_pin_id != acting_user_id:
            raise PermissionError("PIN can only create requests for themselves")

        # Normalize volunteers to JSON text
        data["volunteers"] = json.dumps(self._serialize_volunteers(payload.get("volunteers")))

        created = self.repository.create_request(
            pin_id=data["pin_id"],
            csr_id=data.get("csr_id"),               # usually None at creation
            category_id=data["category_id"],
            district_id=data["district_id"],
            title=data["title"],
            description=data.get("description"),
            start_at=data.get("start_at"),
            end_at=data.get("end_at"),
            volunteers=data.get("volunteers"),
        )
        return created

    # -------------- update (PIN owner only) --------------
    def update_request(self, req_id: int, payload: Dict[str, Any], *, acting_user_id: int, acting_role: str) -> Optional[Dict[str, Any]]:
        if acting_role != "PIN":
            raise PermissionError("Only PIN can update requests")

        current = self.repository.get_request_by_id(req_id)
        if not current:
            return None
        if current.get("pin_id") != acting_user_id:
            raise PermissionError("Forbidden: you can update only your own request")

        # Prevent changing ownership/matching fields here
        for forbidden in ("pin_id", "csr_id"):
            if forbidden in payload:
                raise ValueError(f"Field '{forbidden}' cannot be modified")

        data = dict(payload)
        if "volunteers" in data:
            data["volunteers"] = json.dumps(self._serialize_volunteers(data.get("volunteers")))

        return self.repository.update_request(req_id, **data)

    # -------------- delete (PIN owner OR PlatformManager) --------------
    def delete_request(self, req_id: int, *, acting_user_id: int, acting_role: str) -> bool:
        current = self.repository.get_request_by_id(req_id)
        if not current:
            return False

        if acting_role == "PlatformManager":
            return self.repository.delete_request(req_id)

        if acting_role == "PIN":
            if current.get("pin_id") != acting_user_id:
                raise PermissionError("Forbidden: you can delete only your own request")
            return self.repository.delete_request(req_id)

        raise PermissionError("Forbidden: only owner PIN or PlatformManager can delete requests")
