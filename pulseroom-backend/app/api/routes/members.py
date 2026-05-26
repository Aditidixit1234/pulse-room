from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db.models.user import User
from app.db.models.room import RoomMember
from app.schemas.member import InviteMemberRequest, UpdateRoleRequest
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/members", tags=["members"])

@router.get("")
def get_members(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "initials": u.initials,
            "role": "member",
            "status": "offline",
        }
        for u in users
    ]

@router.post("/invite")
def invite_member(data: InviteMemberRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"Invite sent to {data.email}"}

@router.patch("/{user_id}/role")
def update_role(user_id: str, data: UpdateRoleRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    member = db.query(RoomMember).filter(RoomMember.user_id == user_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.role = data.role
    db.commit()
    return {"message": "Role updated"}