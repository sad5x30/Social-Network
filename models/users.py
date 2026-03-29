from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from database import Base
from sqlalchemy.orm import relationship


class TableUsers(Base):
    __tablename__ = "table_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    avatar = Column(String, nullable=True)
    is_active = Column(Boolean)

    rel_comments = relationship("TableComment", back_populates="rel_comm_user")
    rel_like = relationship("TableLikes", back_populates="rel_like_user")
    rel_posts = relationship("TablePosts", back_populates="user")
    messages = relationship("TableMessages", back_populates="user")
    
    
    rel_subscriptions = relationship(
        "TableSub",
        foreign_keys="TableSub.user",
        back_populates="rel_subscribing_user",
        cascade="all, delete-orphan",
    )
    rel_subscribers = relationship(
        "TableSub",
        foreign_keys="TableSub.sub_user",
        back_populates="rel_target_user",
        cascade="all, delete-orphan",
    )
