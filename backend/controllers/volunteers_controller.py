# backend/controllers/volunteers_controller.py
from typing import Any, Dict, List, Optional
from backend.repositories.volunteers_repository import VolunteersRepository

class VolunteersController:
    """Thin service/controller layer for volunteers."""

    def __init__(self, repo: VolunteersRepository):
        self.repo = repo

    def _validate(self, name: Optional[str], email: Optional[str]) -> Optional[str]:
        if not name or not name.strip():
            return "name is required"
        if not email or not email.strip():
            return "email is required"
        return None

    def list(self, *, company_id: int, q: Optional[str]) -> List[Dict[str, Any]]:
        return self.repo.list(company_id=company_id, q=q)

    def get(self, *, company_id: int, vol_id: int) -> Optional[Dict[str, Any]]:
        return self.repo.get_by_id(vol_id, company_id=company_id)

    def create(self, *, company_id: int, name: str, email: str, phone: Optional[str]) -> Dict[str, Any]:
        err = self._validate(name, email)
        if err:
            return {"error": err}, 400

        # Optional duplicate guard by email within company
        exists = self.repo.get_by_email(company_id=company_id, email=email.strip())
        if exists:
            return {"error": "email already exists in your company"}, 400

        out = self.repo.create(company_id=company_id, name=name.strip(), email=email.strip(), phone=(phone or "").strip() or None)
        return out, 201

    def update(self, *, company_id: int, vol_id: int, name: str, email: str, phone: Optional[str]):
        err = self._validate(name, email)
        if err:
            return {"error": err}, 400

        out = self.repo.update(vol_id, company_id=company_id, name=name.strip(), email=email.strip(), phone=(phone or "").strip() or None)
        if not out:
            return {"error": "not found"}, 404
        return out, 200

    def delete(self, *, company_id: int, vol_id: int):
        ok = self.repo.delete(vol_id, company_id=company_id)
        if not ok:
            return {"error": "not found"}, 404
        return {}, 200
