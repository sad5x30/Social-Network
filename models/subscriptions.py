from database import Base

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

class TableSub(Base):
    __tablename__ = "table_sub"

    id = Column(Integer, primary_key=True)
    
    user = Column(Integer, ForeignKey("table_users.id"), nullable=False)
    sub_user = Column(Integer, ForeignKey("table_users.id"), nullable=False)

    rel_subscribing_user = relationship(
        "TableUsers",
        foreign_keys=[user],
        back_populates="rel_subscriptions",
    )
    rel_target_user = relationship(
        "TableUsers",
        foreign_keys=[sub_user],
        back_populates="rel_subscribers",
    )

    
