from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class Shortlist(BaseModel):
    id: Optional[int] = None
    csr_id: int
    request_id: int
    created_at: Optional[datetime] = None

class ShortlistCreate(BaseModel):
    csr_id: int
    request_id: int
