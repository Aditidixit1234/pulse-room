from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User
from app.db.models.message import Message
from app.schemas.message import SendMessageRequest
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/messages", tags=["messages"])

@router.get("/{conversation_id}")
def get_messages(conversation_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    messages = db.query(Message).filter(Message.room_id == conversation_id).order_by(Message.created_at).all()
    return [
        {
            "id": m.id,
            "text": m.text,
            "sender_id": m.sender_id,
            "sender_name": m.sender.name,
            "sender_initials": m.sender.initials,
            "created_at": m.created_at,
        }
        for m in messages
    ]

@router.post("/{conversation_id}")
def send_message(conversation_id: str, data: SendMessageRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    message = Message(
        text=data.text,
        sender_id=current_user.id,
        room_id=conversation_id,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return {
        "id": message.id,
        "text": message.text,
        "sender_id": message.sender_id,
        "sender_name": current_user.name,
        "sender_initials": current_user.initials,
        "created_at": message.created_at,
    }