from typing import List, Dict, Any, Optional
import json
from backend.repositories.requests_repository import RequestsRepository
from backend.repositories.accounts_repository import AccountsRepository
from backend.repositories.shortlist_repository import ShortlistRepository
from backend.repositories.notifications_repository import NOTIF_MATCH_ASSIGNED, NotificationsRepository

class MatchingController:
    def __init__(self, requests_repo: RequestsRepository, accounts_repo: AccountsRepository, notifications_repo: NotificationsRepository, shortlist_repo: Optional[ShortlistRepository] = None):
        self.requests_repo = requests_repo
        self.accounts_repo = accounts_repo
        self.notifications_repo = notifications_repo
        self.shortlist_repo = shortlist_repo

    @staticmethod
    def _normalize_volunteers(raw) -> List[Any]:
        if not isinstance(raw, list):
            return []
        out = []
        for v in raw:
            if isinstance(v, str):
                s = v.strip()
                if s:
                    out.append(s)
            elif isinstance(v, int):
                out.append(v)
        return out

    def accept_and_assign(self, *, request_id: int, csr_id: int, volunteers: List[int]) -> Dict[str, Any]:
        # 1) Assign CSR – returns bool
        success = self.requests_repo.try_assign_csr(request_id=request_id, csr_id=csr_id)
        if not success:
            return {"error": "Request not found or not assignable"}, 404

        # 2) Normalize and save volunteers as JSON string
        norm_vols = self._normalize_volunteers(volunteers)
        self.requests_repo.update_volunteers(
            request_id=request_id,
            volunteers_json=json.dumps(norm_vols)  # <-- repository expects volunteers_json
        )

        # 3) Reload request row for notification payload
        req = self.requests_repo.get_request_by_id(request_id)
        if not req:
            return {"error": "Request not found after update"}, 404

        # 4) Optional: load CSR name
        csr = self.accounts_repo.get_account_by_id(csr_id) if hasattr(self.accounts_repo, "get_account_by_id") else None
        csr_name = (csr or {}).get("name")

        # 5) Create notification (receiver = PIN user)
        self.notifications_repo.create(
            user_id=req["pin_id"],
            request_id=request_id,
            actor_id=csr_id,
            type=NOTIF_MATCH_ASSIGNED,
            message=f"Your request '{req['title']}' has been accepted by {csr_name or f'CSR #{csr_id}'}."
        )

        # 6) Removed from all shortlists
        if self.shortlist_repo is not None:
            self.shortlist_repo.clear_for_request(request_id)

        # 7) Return updated request
        out = self.requests_repo.get_request_by_id(request_id)
        return out, 200