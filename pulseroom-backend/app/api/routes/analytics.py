from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User
from app.db.models.room import Room, RoomMember
from app.db.models.task import Task
from app.db.models.activity import Activity
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("")
def get_analytics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memberships = db.query(RoomMember).filter(RoomMember.user_id == current_user.id).all()
    room_ids = [m.room_id for m in memberships]

    total_rooms = len(room_ids)
    total_tasks = db.query(Task).filter(Task.room_id.in_(room_ids)).count()
    open_tasks = db.query(Task).filter(Task.room_id.in_(room_ids), Task.status != "done").count()
    done_tasks = db.query(Task).filter(Task.room_id.in_(room_ids), Task.status == "done").count()
    total_members = db.query(User).count()
    total_events = db.query(Activity).filter(Activity.room_id.in_(room_ids)).count()

    room_stats = []
    for room_id in room_ids:
        room = db.query(Room).filter(Room.id == room_id).first()
        if room:
            task_count = db.query(Task).filter(Task.room_id == room_id).count()
            event_count = db.query(Activity).filter(Activity.room_id == room_id).count()
            room_stats.append({
                "id": str(room.id),
                "name": room.name,
                "tasks": task_count,
                "events": event_count,
                "members": len(room.members),
                "color": room.color,
            })

    room_stats.sort(key=lambda x: x["events"], reverse=True)

    return {
        "metrics": {
            "total_rooms": total_rooms,
            "total_tasks": total_tasks,
            "open_tasks": open_tasks,
            "done_tasks": done_tasks,
            "total_members": total_members,
            "total_events": total_events,
        },
        "room_stats": room_stats[:6],
    }