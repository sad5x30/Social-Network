from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from datetime import datetime
from database import Base
from sqlalchemy.orm import relationship


class TableLikes(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user_id = Column(Integer, ForeignKey("table_users.id"), nullable=False, index=True)
    post_id = Column(Integer, ForeignKey("table_posts.id"), nullable=False, index=True)

    __table_args__ = (UniqueConstraint("user_id", "post_id", name="uq_likes_user_post"),)

    rel_like_user = relationship("TableUsers", back_populates="rel_like")
    rel_like_post = relationship("TablePosts", back_populates="rel_like")
