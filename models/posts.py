from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from database import Base
from sqlalchemy.orm import relationship

class TablePosts(Base):
    __tablename__ = "table_posts"

    id = Column(Integer, primary_key=True)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user_id = Column(Integer, ForeignKey("table_users.id"), nullable=False)

    user = relationship("TableUsers", back_populates="rel_posts")
    rel_comments = relationship("TableComment", back_populates="rel_comm_post")
    rel_like = relationship("TableLikes", back_populates="rel_like_post")