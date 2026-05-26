from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class NotificationResponse(BaseModel):
    id: UUID
    title: str
    desc: Optional[str] = None
    icon: str
    room: Optional[str] = None
    unread: bool
    time: str
    created_at: datetime

    class Config:
        from_attributes = True