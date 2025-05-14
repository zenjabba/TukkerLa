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
    
    # Google OAuth settings
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_AUTH_URL: str = "https://accounts.google.com/o/oauth2/auth"
    GOOGLE_TOKEN_URL: str = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL: str = "https://www.googleapis.com/oauth2/v3/userinfo"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings() 