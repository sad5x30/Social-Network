from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class TableComment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("table_users.id"), index=True, nullable=False)
    post_id = Column(Integer, ForeignKey("table_posts.id"), index=True, nullable=False)

    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    rel_comm_user = relationship("TableUsers", back_populates="rel_comments")
    rel_comm_post = relationship("TablePosts", back_populates="rel_comments")