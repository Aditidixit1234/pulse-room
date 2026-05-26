from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User
from app.db.models.room import Room, RoomMember
from app.db.models.task import Task
from app.db.models.note import Note
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/search", tags=["search"])

@router.get("")
def search(
    q: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    results = []

    # Search rooms
    rooms = db.query(Room).filter(Room.name.ilike(f"%{q}%")).limit(5).all()
    for r in rooms:
        results.append({
            "type": "room",
            "id": str(r.id),
            "name": r.name,
            "desc": f"{len(r.members)} members · {len(r.tasks)} tasks",
            "icon": "🏠",
        })

    # Search tasks
    tasks = db.query(Task).filter(Task.title.ilike(f"%{q}%")).limit(5).all()
    for t in tasks:
        results.append({
            "type": "task",
            "id": str(t.id),
            "name": t.title,
            "desc": f"{t.status.replace('_', ' ').title()}",
            "icon": "✅",
        })

    # Search notes
    notes = db.query(Note).filter(Note.title.ilike(f"%{q}%")).limit(5).all()
    for n in notes:
        results.append({
            "type": "note",
            "id": str(n.id),
            "name": n.title,
            "desc": f"Note",
            "icon": "📋",
        })

    # Search members
    members = db.query(User).filter(
        (User.name.ilike(f"%{q}%")) | (User.email.ilike(f"%{q}%"))
    ).limit(5).all()
    for m in members:
        results.append({
            "type": "member",
            "id": str(m.id),
            "name": m.name,
            "desc": m.email,
            "icon": "👤",
        })

    return {"results": results, "total": len(results)}