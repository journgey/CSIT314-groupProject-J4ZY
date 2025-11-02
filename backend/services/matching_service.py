# backend/services/matching_service.py
from typing import List, Dict, Any
import json
from backend.repositories.requests_repository import RequestsRepository
from backend.repositories.accounts_repository import AccountsRepository

class MatchingService:
    """
    - Accept: allowed only when computed_status == 'pending' (now < start_at and no CSR)
      * Atomic update via repo.try_assign_csr
      * If already accepted by same CSR: idempotent OK (return current row)
      * If accepted by another CSR: error
    - Assign volunteers: store as-is (list of strings or ids) into requests.volunteers (JSON text)
      * No DB-side validation because there is no volunteers table by design.
    """

    def __init__(self, requests_repo: RequestsRepository, accounts_repo: AccountsRepository):
        self.requests_repo = requests_repo
        self.accounts_repo = accounts_repo

    # --------- helpers ----------
    @staticmethod
    def _normalize_volunteers(raw) -> List[Any]:
        """
        Accepts list of strings/ints; returns list (no casting other than trimming strings).
        Example accepted payloads:
          ["Alice", "Bob"]  or  [101, 102]
        """
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

    # --------- actions ----------
    def accept_request(self, *, csr_id: int, request_id: int) -> Dict[str, Any]:
        req = self.requests_repo.get_request_by_id(request_id)
        if not req:
            raise ValueError("Request not found")

        status = (req.get("computed_status") or req.get("status") or "").lower()
        current_owner = req.get("csr_id")

        # already owned by another CSR
        if current_owner is not None and current_owner != csr_id:
            raise ValueError("This request has already been accepted by another CSR")

        # already owned by same CSR -> idempotent OK
        if current_owner == csr_id:
            return req

        # allow only when pending
        if status != "pending":
            raise ValueError("Request cannot be accepted in its current status")

        # atomic take
        if not self.requests_repo.try_assign_csr(request_id=request_id, csr_id=csr_id):
            raise ValueError("This request has already been accepted by another CSR")

        return self.requests_repo.get_request_by_id(request_id)

    def assign_volunteers(self, *, csr_id: int, request_id: int, volunteers: List[Any]) -> Dict[str, Any]:
        """
        Save volunteers for an 'accepted' request.
        Without a volunteers table, we store the given list as JSON text.
        """
        req = self.requests_repo.get_request_by_id(request_id)
        if not req:
            raise ValueError("Request not found")

        if (req.get("computed_status") or req.get("status") or "").lower() != "accepted":
            raise ValueError("Assign not allowed before accept")

        if req.get("csr_id") != csr_id:
            raise ValueError("Only the owner CSR can assign volunteers")

        normalized = self._normalize_volunteers(volunteers)
        return self.requests_repo.save_request_volunteers(
            request_id=request_id,
            volunteers_json=json.dumps(normalized),
        )
