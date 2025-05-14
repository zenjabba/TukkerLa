from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import relationship
from app.database import Base


class UsageHistory(Base):
    __tablename__ = "usage_history"

    usage_id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.item_id", ondelete="SET NULL"))
    quantity = Column(Integer, nullable=False)
    used_by = Column(Integer, ForeignKey("users.user_id"))
    usage_date = Column(TIMESTAMP(timezone=True), 
                        server_default=text('now()'), 
                        nullable=False)
    notes = Column(Text)
    
    # Relationships
    used_by_user = relationship("User")
    item = relationship("Item") 