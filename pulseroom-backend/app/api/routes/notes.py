from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from pydantic import BaseModel
from typing import Optional
from app.db.database import get_db
from app.db.models.user import User
from app.db.models.note import Note
from app.core.dependencies import get_current_user
from datetime import datetime

router = APIRouter(prefix="/rooms/{room_id}/notes", tags=["notes"])

class CreateNoteRequest(BaseModel):
    title: str
    content: Optional[str] = None

class UpdateNoteRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

def format_time(dt: datetime) -> str:
    diff = (datetime.utcnow() - dt).total_seconds()
    if diff < 60: return "Just now"
    if diff < 3600: return f"{int(diff//60)} min ago"
    if diff < 86400: return f"{int(diff//3600)} hr ago"
    return f"{int(diff//86400)} days ago"

@router.get("")
def get_notes(room_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notes = db.query(Note).filter(Note.room_id == room_id).order_by(Note.updated_at.desc()).all()
    return [
        {
            "id": n.id,
            "title": n.title,
            "content": n.content,
            "room_id": n.room_id,
            "created_by": n.created_by,
            "time": format_time(n.updated_at),
            "created_at": n.created_at,
            "updated_at": n.updated_at,
        }
        for n in notes
    ]

@router.post("")
def create_note(room_id: str, data: CreateNoteRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    note = Note(
        title=data.title,
        content=data.content,
        room_id=room_id,
        created_by=current_user.id,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "room_id": note.room_id,
        "time": "Just now",
        "created_at": note.created_at,
    }

@router.patch("/{note_id}")
def update_note(room_id: str, note_id: str, data: UpdateNoteRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id, Note.room_id == room_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if data.title: note.title = data.title
    if data.content: note.content = data.content
    note.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Note updated"}

@router.delete("/{note_id}")
def delete_note(room_id: str, note_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return {"message": "Note deleted"}