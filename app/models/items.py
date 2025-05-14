from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import relationship
from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)


class Location(Base):
    __tablename__ = "locations"

    location_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)


class Item(Base):
    __tablename__ = "items"

    item_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    barcode = Column(String(50), index=True)
    category_id = Column(Integer, ForeignKey("categories.category_id"))
    location_id = Column(Integer, ForeignKey("locations.location_id"))
    quantity = Column(Integer, default=1)
    stored_date = Column(TIMESTAMP(timezone=True), 
                          server_default=text('now()'), 
                          nullable=False)
    expiry_date = Column(TIMESTAMP(timezone=True))
    notes = Column(Text)
    added_by = Column(Integer, ForeignKey("users.user_id"))
    storage_location = Column(String(20), default='freezer')  # 'freezer', 'fridge', 'pantry'
    min_quantity = Column(Integer, default=1)  # For low stock alerts
    unit = Column(String(20))  # e.g., grams, ml, pieces
    created_at = Column(TIMESTAMP(timezone=True), 
                        server_default=text('now()'), 
                        nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), 
                        server_default=text('now()'),
                        onupdate=text('now()'), 
                        nullable=False)
    
    # Relationships
    category = relationship("Category")
    location = relationship("Location")
    added_by_user = relationship("User")
    images = relationship("Image", back_populates="item") 