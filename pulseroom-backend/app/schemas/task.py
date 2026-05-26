from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class CreateTaskRequest(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "todo"
    priority: str = "medium"
    tag: Optional[str] = None
    due_date: Optional[str] = None
    assignee_id: Optional[UUID] = None

class UpdateTaskRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    tag: Optional[str] = None
    due_date: Optional[str] = None
    assignee_id: Optional[UUID] = None

class TaskResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    tag: Optional[str] = None
    due_date: Optional[str] = None
    room_id: UUID
    assignee_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True