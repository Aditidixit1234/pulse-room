from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User
from app.db.models.notification import Notification
from app.core.dependencies import get_current_user
from datetime import datetime

router = APIRouter(prefix="/notifications", tags=["notifications"])

def format_time(dt: datetime) -> str:
    diff = (datetime.utcnow() - dt).total_seconds()
    if diff < 60: return "Just now"
    if diff < 3600: return f"{int(diff//60)} min ago"
    if diff < 86400: return f"{int(diff//3600)} hr ago"
    return f"{int(diff//86400)} days ago"

@router.get("")
def get_notifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notifs = db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).all()
    return [
        {
            "id": n.id,
            "title": n.title,
            "desc": n.desc,
            "icon": n.icon,
            "room": n.room,
            "unread": n.unread,
            "time": format_time(n.created_at),
            "created_at": n.created_at,
        }
        for n in notifs
    ]

@router.patch("/{notif_id}/read")
def mark_read(notif_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notif = db.query(Notification).filter(Notification.id == notif_id).first()
    if notif:
        notif.unread = False
        db.commit()
    return {"message": "Marked as read"}

@router.patch("/read-all")
def mark_all_read(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.unread == True
    ).update({"unread": False})
    db.commit()
    return {"message": "All marked as read"}