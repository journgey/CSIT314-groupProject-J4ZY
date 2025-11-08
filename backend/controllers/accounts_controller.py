import sqlite3
from typing import Dict, Any, Optional, List
from werkzeug.security import generate_password_hash
from backend.schemas.accounts import Account

class AccountController:

    def __init__(self, repository):
        self.repository = repository

    @staticmethod
    def _require_ua(role: Optional[str]):
        if role != "UserAdmin":
            raise PermissionError("UserAdmin role required")

    @staticmethod
    def _strip_password(record: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if record is None:
            return None
        r = dict(record)
        r.pop("password", None)
        return r

    @classmethod
    def _strip_password_list(cls, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [cls._strip_password(i) for i in items]

    def create_account(self, data: Dict[str, Any]):
        role = (data.get("role") or "").strip()
        company_name = (data.get("company_name") or "").strip()
        company_id = data.get("company_id")
        if role == "CSR":
            if not company_id:
                if not company_name:
                    raise ValueError("CSR accounts must include company_name.")
                company = self.repository.get_company_by_name(company_name)
                if not company:
                    try:
                        company = self.repository.create_company(company_name)
                    except sqlite3.IntegrityError:
                        company = self.repository.get_company_by_name(company_name)
                if not company:
                    raise ValueError("Failed to resolve company_id from company_name.")
                company_id = company["id"]

            data["company_id"] = company_id

        account = Account(**data)

        existing = self.repository.get_account_by_email(account.email)
        if existing:
            raise ValueError("Email already registered.")
                             
        hashed_pw = generate_password_hash(account.password)
        account.password = hashed_pw

        created = self.repository.create_account(
            email=account.email, 
            password=account.password, 
            name=account.name,
            phone=account.phone, 
            role=account.role, 
            status=account.status,
            company_id=account.company_id
        )

        created_fresh = self.repository.get_account_by_id(created["id"])
        return self._strip_password(created_fresh)

    def get_account_by_id(self, account_id: int, *, acting_role: Optional[str] = None) -> Optional[Dict[str, Any]]:
        self._require_ua(acting_role)
        found = self.repository.get_account_by_id(account_id)
        return self._strip_password(found)

    def list_accounts(self, acting_role: Optional[str] = None):
        self._require_ua(acting_role)
        rows = self.repository.list_accounts()
        return self._strip_password_list(rows)

    def update_account(self, account_id: int, data: Dict[str, Any], *, acting_role: Optional[str] = None) -> Optional[Dict[str, Any]]:
        self._require_ua(acting_role)
        if acting_role != "UserAdmin":
            raise PermissionError("UserAdmin role required to update accounts")

        current = self.repository.get_account_by_id(account_id)
        if not current:
            return None
        
        if "password" in data and data["password"]:
            data["password"] = generate_password_hash(data["password"])

        if "email" in data and data["email"]:
            other = self.repository.get_account_by_email(data["email"])
            if other and other.get("id") != account_id:
                raise ValueError("Email already registered.")

        merged = {**current, **data}
        Account(**merged)  
        self.repository.update_account(account_id, **data)  
        updated = self.repository.get_account_by_id(account_id)
        return self._strip_password(updated)

    def delete_account(self, account_id: int, *, acting_role: Optional[str] = None):
        self._require_ua(acting_role)
        try:
            self.repository.delete_account(account_id)
            return True
        except ValueError:
            return False