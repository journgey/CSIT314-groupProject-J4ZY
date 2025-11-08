from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from backend.db_session import get_db
from backend.repositories.geo_repository import GeoRepository
from backend.controllers.address_controller import AddressController
from backend.controllers.notifications_controller import NotificationsController
from backend.repositories.notifications_repository import NotificationsRepository
from backend.repositories.accounts_repository import AccountsRepository



class RequestsController:
    def __init__(self, repository):
        self.repository = repository

    @staticmethod
    def _serialize_volunteers(vols):
        if vols is None:
            return []
        if isinstance(vols, list):
            return vols
        if isinstance(vols, str) and vols.strip():
            return [int(x) for x in vols.split(",") if x.strip().isdigit()]
        return []

    @staticmethod
    def _parse_dt(s: Optional[str]) -> Optional[datetime]:
        if not s:
            return None
        t = s.strip().replace("T", " ")
        if len(t) == 16:
            t = t + ":00"
        return datetime.fromisoformat(t)

    @staticmethod
    def _assert_valid_period(
        start_at_new: Optional[str],
        end_at_new: Optional[str],
        *,
        start_at_old: Optional[str],
        end_at_old: Optional[str],
    ) -> None:
        s = RequestsController._parse_dt(start_at_new) or RequestsController._parse_dt(start_at_old)
        e = RequestsController._parse_dt(end_at_new) or RequestsController._parse_dt(end_at_old)
        if s and e and e < s:
            raise ValueError("end_at must be greater than or equal to start_at")

    def get_request_by_id(self, req_id: int) -> Optional[Dict[str, Any]]:
        item = self.repository.get_request_by_id(req_id)
        if not item:
            return None
        try:
            if self.repository.increment_view_count(req_id):
                try:
                    item["view_count"] = (item.get("view_count") or 0) + 1
                except Exception:
                    pass
        except Exception:
            pass

        return item

    def list_requests(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return self.repository.list_requests(filters or {})

    def create_request(
        self,
        payload: Dict[str, Any],
        *,
        acting_user_id: int,
        acting_role: str,
    ) -> Dict[str, Any]:
        if (acting_role or "").upper() != "PIN":
            raise PermissionError("Only PIN can create requests")

        self._assert_valid_period(
            payload.get("start_at"),
            payload.get("end_at"),
            start_at_old=None,
            end_at_old=None,
        )

        payload = AddressController(GeoRepository(get_db())).enrich_request_payload(payload)

        data = dict(payload)
        provided_pin_id = data.get("pin_id")
        if provided_pin_id is None:
            data["pin_id"] = acting_user_id
        elif provided_pin_id != acting_user_id:
            raise PermissionError("PIN can only create requests for themselves")

        data["volunteers"] = json.dumps(self._serialize_volunteers(payload.get("volunteers")))

        created = self.repository.create_request(
            pin_id=data["pin_id"],
            csr_id=data.get("csr_id"),
            category_id=data["category_id"],
            district_id=data["district_id"],
            title=data["title"],
            description=data.get("description"),
            start_at=data.get("start_at"),
            end_at=data.get("end_at"),
            volunteers=data.get("volunteers"),
        )
        return created

    def update_request(
        self,
        req_id: int,
        payload: Dict[str, Any],
        *,
        acting_user_id: int,
        acting_role: str,
    ) -> Optional[Dict[str, Any]]:
        if (acting_role or "").upper() != "PIN":
            raise PermissionError("Only PIN can update requests")

        current = self.repository.get_request_by_id(req_id)
        if not current:
            return None
        if current.get("pin_id") != acting_user_id:
            raise PermissionError("Forbidden: you can update only your own request")

        self._assert_valid_period(
            payload.get("start_at"),
            payload.get("end_at"),
            start_at_old=current.get("start_at"),
            end_at_old=current.get("end_at"),
        )

        for forbidden in ("pin_id", "csr_id"):
            if forbidden in payload:
                raise ValueError(f"Field '{forbidden}' cannot be modified")

        data = dict(payload)
        if "volunteers" in data:
            data["volunteers"] = json.dumps(self._serialize_volunteers(data.get("volunteers")))

        return self.repository.update_request(req_id, **data)

    def delete_request(
        self,
        req_id: int,
        *,
        acting_user_id: int,
        acting_role: str,
    ) -> bool:
        current = self.repository.get_request_by_id(req_id)
        if not current:
            return False

        role = (acting_role or "").upper()
        if role == "PLATFORMMANAGER":
            return self.repository.delete_request(req_id)

        if role == "PIN":
            if current.get("pin_id") != acting_user_id:
                raise PermissionError("Forbidden: you can delete only your own request")
            
            csr_id = current.get("csr_id")
            if csr_id is not None:
                conn = get_db()
                nsvc = NotificationsController(NotificationsRepository(conn))
                actor_name = AccountsRepository(conn).get_account_by_id(acting_user_id)["name"]
                nsvc.create_for_pin_deleted_request(
                    csr_user_id=csr_id,
                    actor_name=actor_name,
                    request_title=current["title"],
                    request_id=current["id"],
                    actor_id=acting_user_id,
                )

            return self.repository.delete_request(req_id)

        raise PermissionError("Forbidden: only owner PIN or PlatformManager can delete requests")
