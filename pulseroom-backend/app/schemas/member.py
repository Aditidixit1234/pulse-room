from pydantic import BaseModel, EmailStr
from uuid import UUID

class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: str = "member"

class UpdateRoleRequest(BaseModel):
    role: str

class MemberResponse(BaseModel):
    user_id: UUID
    name: str
    email: str
    initials: str
    role: str
    status: str = "offline"

    class Config:
        from_attributes = True