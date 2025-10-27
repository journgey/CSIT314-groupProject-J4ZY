from typing import Optional
from pydantic import BaseModel, EmailStr, model_validator
from .common import AccountRole, AccountStatus

class Account(BaseModel):
    id: Optional[int] = None
    email: EmailStr
    password: str
    name: Optional[str] = None
    phone: Optional[str] = None
    role: AccountRole
    status: AccountStatus = AccountStatus.active
    company_id: Optional[int] = None

    @model_validator(mode="after")
    def _company_rule(self):
        """CSR must have company_id; non-CSR must not have company_id."""
        if self.role == AccountRole.CSR and self.company_id is None:
            raise ValueError("CSR accounts must have a company_id.")
        if self.role != AccountRole.CSR and self.company_id is not None:
            raise ValueError("Only CSR accounts can have company_id.")
        return self
