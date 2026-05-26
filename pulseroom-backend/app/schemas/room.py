from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class CreateRoomRequest(BaseModel):
    name: str
    description: Optional[str] = None
    color: str = "#4dffb8"

class UpdateRoomRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None

class RoomResponse(BaseModel):
    id: UUID
    name: str
    initials: str
    description: Optional[str] = None
    color: str
    is_live: bool
    member_count: int = 0
    task_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True