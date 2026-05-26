from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class SendMessageRequest(BaseModel):
    text: str

class MessageResponse(BaseModel):
    id: UUID
    text: str
    sender_id: UUID
    sender_name: str
    sender_initials: str
    room_id: Optional[UUID] = None
    receiver_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True