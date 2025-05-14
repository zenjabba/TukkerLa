from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql.expression import text
from app.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(100), nullable=True)  # Made nullable to support OAuth users
    is_admin = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), 
                         server_default=text('now()'), 
                         nullable=False)
    
    # Google OAuth fields
    google_id = Column(String(100), unique=True, nullable=True)
    picture = Column(String(255), nullable=True)
    auth_provider = Column(String(20), default="local")  # "local" or "google" 