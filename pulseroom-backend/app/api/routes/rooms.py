from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db.models.user import User
from app.db.models.room import Room, RoomMember
from app.schemas.room import CreateRoomRequest, UpdateRoomRequest, RoomResponse
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/rooms", tags=["rooms"])

@router.get("", response_model=List[RoomResponse])
def get_rooms(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memberships = db.query(RoomMember).filter(RoomMember.user_id == current_user.id).all()
    room_ids = [m.room_id for m in memberships]
    rooms = db.query(Room).filter(Room.id.in_(room_ids)).all()
    result = []
    for room in rooms:
        result.append({
            "id": room.id,
            "name": room.name,
            "initials": room.initials,
            "description": room.description,
            "color": room.color,
            "is_live": room.is_live,
            "member_count": len(room.members),
            "task_count": len(room.tasks),
            "created_at": room.created_at,
        })
    return result

@router.post("", response_model=RoomResponse)
def create_room(data: CreateRoomRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    room = Room(
        name=data.name,
        description=data.description,
        color=data.color,
        created_by=current_user.id,
    )
    db.add(room)
    db.flush()

    member = RoomMember(room_id=room.id, user_id=current_user.id, role="owner")
    db.add(member)
    db.commit()
    db.refresh(room)

    return {
        "id": room.id,
        "name": room.name,
        "initials": room.initials,
        "description": room.description,
        "color": room.color,
        "is_live": room.is_live,
        "member_count": 1,
        "task_count": 0,
        "created_at": room.created_at,
    }

@router.get("/{room_id}", response_model=RoomResponse)
def get_room(room_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return {
        "id": room.id,
        "name": room.name,
        "initials": room.initials,
        "description": room.description,
        "color": room.color,
        "is_live": room.is_live,
        "member_count": len(room.members),
        "task_count": len(room.tasks),
        "created_at": room.created_at,
    }

@router.patch("/{room_id}")
def update_room(room_id: str, data: UpdateRoomRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if data.name: room.name = data.name
    if data.description: room.description = data.description
    if data.color: room.color = data.color
    db.commit()
    return {"message": "Room updated"}

@router.delete("/{room_id}")
def delete_room(room_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    db.delete(room)
    db.commit()
    return {"message": "Room deleted"}