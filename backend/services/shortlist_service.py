# backend/services/shortlist_service.py
from typing import Any, Dict, List, Optional

class ShortlistService:
    def __init__(self, shortlist_repo, accounts_repo=None, requests_repo=None):
        self.shortlist_repo = shortlist_repo
        self.accounts_repo = accounts_repo
        self.requests_repo = requests_repo

    # Create
    def add_to_shortlist(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        csr_id = payload.get("csr_id")
        request_id = payload.get("request_id")

        if not isinstance(csr_id, int) or not isinstance(request_id, int):
            raise ValueError("csr id and request id must be integers")

        # check exist
        if self.accounts_repo:
            csr = self.accounts_repo.get_by_id(csr_id)
            if not csr or csr.get("role") != "CSR":
                raise ValueError("CSR account not found or invalid role")
        if self.requests_repo:
            req = self.requests_repo.get_request_by_id(request_id)
            if not req:
                raise ValueError("Request not found")

        # prevnet dup
        exists = self.shortlist_repo.get_by_pair(csr_id=csr_id, request_id=request_id)
        if exists:
            return {"id": exists["id"], "csr_id": csr_id, "request_id": request_id, "duplicate": True}

        return self.shortlist_repo.insert(csr_id=csr_id, request_id=request_id)

    # Read (collection)
    def list_shortlist(self, csr_id: int) -> List[Dict[str, Any]]:
        if not isinstance(csr_id, int):
            raise ValueError("csr id must be an integer")
        return self.shortlist_repo.list_by_csr(csr_id)

    # Delete
    def remove_shortlist(self, shortlist_id: int) -> Dict[str, Any]:
        if not isinstance(shortlist_id, int):
            raise ValueError("shortlist id must be an integer")
        ok = self.shortlist_repo.delete(shortlist_id)
        if not ok:
            raise ValueError("Shortlist item not found")
        return {"deleted_id": shortlist_id}

    # (옵션) 쌍 기준 삭제
    def remove_shortlist_by_pair(self, *, csr_id: int, request_id: int) -> Dict[str, Any]:
        ok = self.shortlist_repo.delete_by_pair(csr_id=csr_id, request_id=request_id)
        if not ok:
            raise ValueError("Shortlist pair not found")
        return {"deleted": True, "csr_id": csr_id, "request_id": request_id}
