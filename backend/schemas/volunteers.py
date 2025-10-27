from typing import Optional
from pydantic import BaseModel, EmailStr

class Volunteer(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company_id: Optional[int] = None
