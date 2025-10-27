from __future__ import annotations
from typing import Optional, List, Annotated
from datetime import datetime
from pydantic import BaseModel, field_validator, model_validator, StringConstraints
from .common import RequestStatus  # pending/accepted/completed/expired 등 Enum

# Use Annotated + StringConstraints instead of constr(...)
TitleStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

class Request(BaseModel):
    id: Optional[int] = None
    pin_id: int
    csr_id: Optional[int] = None
    category_id: int
    district_id: int
    title: TitleStr
    description: Optional[str] = None
    status: RequestStatus
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    volunteers: Optional[List[int]] = None  # normalized to [] below

    # --- Field-level normalization ---

    @field_validator("volunteers", mode="before")
    @classmethod
    def _normalize_volunteers(cls, v):
        """Normalize None/blank to empty list; accept comma-separated string."""
        if v is None:
            return []
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return []
            return [int(x) for x in s.split(",") if x.strip().isdigit()]
        return v

    # --- Model-level invariants that need multiple fields ---

    @model_validator(mode="after")
    def _check_time_order(self):
        """Ensure end_at is not earlier than start_at."""
        if self.end_at and self.start_at and self.end_at < self.start_at:
            raise ValueError("end_at cannot be earlier than start_at.")
        return self

    @model_validator(mode="after")
    def _status_constraints(self):
        """
        Enforce consistency between status, csr_id, and volunteers:
        - pending/expired: csr_id must be None, volunteers must be empty.
        - accepted/completed: csr_id required, at least 1 volunteer.
        """
        vols = self.volunteers or []
        if self.status in (RequestStatus.pending, RequestStatus.expired):
            if self.csr_id is not None:
                raise ValueError("csr_id must be NULL for pending/expired requests.")
            if len(vols) != 0:
                raise ValueError("volunteers must be empty for pending/expired requests.")
        elif self.status in (RequestStatus.accepted, RequestStatus.completed):
            if self.csr_id is None:
                raise ValueError("csr_id is required for accepted/completed requests.")
            if len(vols) < 1:
                raise ValueError("At least one volunteer is required for accepted/completed requests.")
        return self
