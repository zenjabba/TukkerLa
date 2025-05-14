from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import relationship
from app.database import Base


class BarcodeProduct(Base):
    __tablename__ = "barcode_products"

    barcode_id = Column(Integer, primary_key=True, index=True)
    barcode = Column(String(50), unique=True, nullable=False, index=True)
    product_name = Column(String(100), nullable=False)
    default_category_id = Column(Integer, ForeignKey("categories.category_id"))
    default_expiry_days = Column(Integer)
    created_at = Column(TIMESTAMP(timezone=True), 
                         server_default=text('now()'), 
                         nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), 
                        server_default=text('now()'),
                        onupdate=text('now()'), 
                        nullable=False)
    
    # Relationships
    default_category = relationship("Category") 