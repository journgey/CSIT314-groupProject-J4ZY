from typing import Dict, Any
from werkzeug.security import check_password_hash
from backend.repositories.auth_repository import AuthRepository

class AuthController:
    def __init__(self, repo: AuthRepository):
        self.repo = repo

    def login(self, email: str, password: str) -> Dict[str, Any]:
        acct = self.repo.find_by_email(email)
        if not acct or not check_password_hash(acct["password"], password):
            raise ValueError("Invalid email or password")
        if acct.get("status") != "active":
            raise ValueError("Account inactive")

        return {
            "id": acct["id"],
            "role": acct.get("role"),
            "company_id": acct.get("company_id"),
            "name": acct.get("name"),
            "email": acct.get("email"),
        }