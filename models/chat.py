from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from datetime import datetime
from database import Base
from sqlalchemy.orm import relationship

class TableChats(Base):
    __tablename__ = "table_chats"
    __table_args__ = (
        UniqueConstraint("user1_id", "user2_id", name="uq_chat_user_pair"),
        CheckConstraint("user1_id <> user2_id", name="ck_chat_not_self"),
    )

    id = Column(Integer, primary_key=True)
    user1_id = Column(Integer, ForeignKey("table_users.id"), nullable=False)
    user2_id = Column(Integer, ForeignKey("table_users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("TableMessages", back_populates="chat")
    user_1 = relationship(
        "TableUsers",
        foreign_keys=[user1_id],
        back_populates="chat_1"
    )

    user_2 = relationship(
        "TableUsers",
        foreign_keys=[user2_id],
        back_populates="chat_2",
    )


    