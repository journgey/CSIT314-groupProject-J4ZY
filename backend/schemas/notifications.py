from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class Notification(BaseModel):
    id: Optional[int] = None
    user_id: int
    message: str = Field(min_length=1)
    request_id: Optional[int] = None
    actor_id: Optional[int] = None
    read_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

class NotificationCreate(BaseModel):
    user_id: int
    message: str = Field(min_length=1)
    request_id: Optional[int] = None
    actor_id: Optional[int] = None

class NotificationReadToggle(BaseModel):
    notification_id: int
