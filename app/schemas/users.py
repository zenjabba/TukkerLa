from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: Optional[str] = Field(None, min_length=8)
    auth_provider: Optional[str] = "local"
    google_id: Optional[str] = None
    picture: Optional[str] = None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    is_admin: Optional[bool] = None
    picture: Optional[str] = None


class UserInDB(UserBase):
    user_id: int
    is_admin: bool
    created_at: datetime
    auth_provider: str = "local"
    picture: Optional[str] = None

    class Config:
        orm_mode = True


class User(UserInDB):
    pass


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    
    
class GoogleAuthRequest(BaseModel):
    code: str
    redirect_uri: str 