from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import relationship
from app.database import Base


class Image(Base):
    __tablename__ = "images"

    image_id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.item_id", ondelete="CASCADE"))
    image_path = Column(String, nullable=False)
    is_primary = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), 
                         server_default=text('now()'), 
                         nullable=False)
    
    # Relationships
    item = relationship("Item", back_populates="images") 