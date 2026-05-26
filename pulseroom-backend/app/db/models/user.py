import uuid
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    image = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    room_members = relationship("RoomMember", back_populates="user")
    tasks = relationship(
        "Task",
        foreign_keys="[Task.assignee_id]",
        back_populates="assignee"
    )
    messages = relationship(
        "Message",
        foreign_keys="[Message.sender_id]",
        back_populates="sender"
    )
    notifications = relationship("Notification", back_populates="user")

    @property
    def initials(self):
        parts = self.name.split()
        return ''.join(p[0] for p in parts[:2]).upper()