from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User
from app.db.models.activity import Activity
from app.core.dependencies import get_current_user
from datetime import datetime

router = APIRouter(prefix="/rooms/{room_id}/activity", tags=["activity"])

def format_time(dt: datetime) -> str:
    diff = (datetime.utcnow() - dt).total_seconds()
    if diff < 60: return "Just now"
    if diff < 3600: return f"{int(diff//60)} min ago"
    if diff < 86400: return f"{int(diff//3600)} hr ago"
    return f"{int(diff//86400)} days ago"

@router.get("")
def get_activity(room_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    activities = db.query(Activity).filter(
        Activity.room_id == room_id
    ).order_by(Activity.created_at.desc()).limit(50).all()
    return [
        {
            "id": a.id,
            "user_id": a.user_id,
            "user_name": a.user.name,
            "user_initials": a.user.initials,
            "action": a.action,
            "target": a.target,
            "room_id": a.room_id,
            "time": format_time(a.created_at),
            "created_at": a.created_at,
        }
        for a in activities
    ]