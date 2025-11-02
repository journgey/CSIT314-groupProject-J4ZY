from __future__ import annotations
from typing import Optional, List, Annotated
from datetime import datetime
from pydantic import BaseModel, field_validator, model_validator, StringConstraints, Field

TitleStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

class Request(BaseModel):
    id: Optional[int] = None
    pin_id: int
    csr_id: Optional[int] = None
    category_id: int
    district_id: int
    title: TitleStr
    description: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    # stored as JSON text in DB; use list[int] in app
    volunteers: Optional[List[int]] = None

    # feedback fields in DB
    feedback_comment: Optional[str] = None
    feedback_rating: Optional[int] = Field(default=None, ge=1, le=5)
    feedback_created_at: Optional[datetime] = None

    @field_validator("volunteers", mode="before")
    @classmethod
    def _normalize_volunteers(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return []
            return [int(x) for x in s.split(",") if x.strip().isdigit()]
        return v

    @model_validator(mode="after")
    def _check_time_order(self):
        if self.end_at and self.start_at and self.end_at < self.start_at:
            raise ValueError("end_at cannot be earlier than start_at.")
        return self

class RequestWithStatus(Request):
    computed_status: str
