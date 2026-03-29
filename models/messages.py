from sqlalchemy import Column, Integer, DateTime, String, ForeignKey
from sqlalchemy.orm import relationship

from datetime import datetime
from database import Base

class TableMessages(Base):
    __tablename__ = "table_messages"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("table_users.id"), nullable=False)
    text = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    chat = relationship("Chat", back_populates="messages")
    user = relationship("TableUsers", back_populates="messages")