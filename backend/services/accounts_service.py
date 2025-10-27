from typing import Dict, Any, Optional, List
from werkzeug.security import generate_password_hash
from schemas.accounts import Account

class AccountService:
    """Business logic for accounts."""

    def __init__(self, repository):
        self.repository = repository

    @staticmethod
    def _strip_password(record: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Remove password from a single record before returning to clients."""
        if record is None:
            return None
        r = dict(record)
        r.pop("password", None)
        return r

    @classmethod
    def _strip_password_list(cls, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove password from a list of records."""
        return [cls._strip_password(i) for i in items]

    def create_account(self, data: Dict[str, Any]):
        # Validate with schema
        account = Account(**data)

        # Example business rules
        if account.role == "CSR" and not account.company_id:
            raise ValueError("CSR accounts must include company_id.")

        # Check for duplicate email
        existing = self.repository.get_account_by_email(account.email)
        if existing:
            raise ValueError("Email already registered.")
                             
        # Hash password before saving
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

        # Return freshly-read row without password to avoid leaking hash
        created_fresh = self.repository.get_account_by_id(created["id"])
        return self._strip_password(created_fresh)

    def get_account_by_id(self, account_id: int) -> Optional[Dict[str, Any]]:
        found = self.repository.get_account_by_id(account_id)
        return self._strip_password(found)

    def list_accounts(self):
        rows = self.repository.list_accounts()
        return self._strip_password_list(rows)

    def update_account(self, account_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        current = self.repository.get_account_by_id(account_id)
        if not current:
            return None

        # If changing password, always re-hash
        if "password" in data and data["password"]:
            data["password"] = generate_password_hash(data["password"])

        # If changing email, check duplication against other accounts
        if "email" in data and data["email"]:
            other = self.repository.get_account_by_email(data["email"])
            if other and other.get("id") != account_id:
                raise ValueError("Email already registered.")

        # Merge to validate business rules (role/company_id etc.) via schema
        merged = {**current, **data}
        Account(**merged)  # validation only; repository returns the persisted row

        # Perform update (repo returns {"updated_id": ...} per current implementation)
        self.repository.update_account(account_id, **data)  # :contentReference[oaicite:3]{index=3}

        # Read back the updated row to return as payload (common REST pattern)
        updated = self.repository.get_account_by_id(account_id)
        return self._strip_password(updated)

    def delete_account(self, account_id):
        try:
            self.repository.delete_account(account_id)  # raises ValueError if not found
            return True
        except ValueError:
            # Normalize to boolean for controller -> 404
            return False
    

    # --- search APIs ---

    def get_account_by_email(self, email: str):
        """Return single account by email or raise if not found (optional)."""
        acc = self.repository.get_account_by_email(email)
        return self._strip_password(acc)

    def search_accounts_by_name(self, name: str, partial: bool = True):
        """Return a list of accounts matched by name (0..N results)."""
        rows = self.repository.search_accounts_by_name(name=name, partial=partial)
        return self._strip_password_list(rows)