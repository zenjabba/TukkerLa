import os
from pydantic import BaseSettings, SecretStr, EmailStr, validator
from typing import Optional


class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "postgresql://postgres:password@localhost/tuckerla"
    
    # Security settings
    SECRET_KEY: str = "YOUR_SECRET_KEY_HERE_CHANGE_THIS_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Image storage
    UPLOAD_DIRECTORY: str = "static/images"
    
    # Optional barcode API
    BARCODE_API_KEY: Optional[str] = None
    BARCODE_API_URL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings() 