from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Dict, Any, Optional

from app.database import get_db
from app.models.users import User
from app.schemas.users import UserCreate, User as UserSchema, Token, GoogleAuthRequest
from app.services.auth import (
    authenticate_user, 
    create_access_token, 
    get_password_hash, 
    get_current_user
)
from app.services.google_auth import (
    exchange_code_for_token,
    get_google_user_info,
    authenticate_google_user
)
from app.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserSchema)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if username already exists
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    if user.auth_provider == "local":
        if not user.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is required for local authentication"
            )
        hashed_password = get_password_hash(user.password)
    else:
        hashed_password = None
    
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        auth_provider=user.auth_provider,
        google_id=user.google_id,
        picture=user.picture,
        is_admin=False  # Default to non-admin
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate user and provide JWT token.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token with user info
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.user_id},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserSchema)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@router.get("/google/url")
async def get_google_auth_url(redirect_uri: str):
    """
    Get the Google authorization URL.
    The client will redirect the user to this URL for authentication.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured"
        )
    
    auth_url = (
        f"{settings.GOOGLE_AUTH_URL}?"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope=email+profile&"
        f"access_type=offline"
    )
    
    return {"auth_url": auth_url}


@router.post("/google/callback")
async def google_auth_callback(
    request: GoogleAuthRequest,
    db: Session = Depends(get_db)
):
    """
    Handle the Google OAuth callback.
    Exchange the authorization code for an access token,
    get the user info, and authenticate the user.
    """
    # Exchange authorization code for access token
    token_data = await exchange_code_for_token(request.code, request.redirect_uri)
    
    # Get user info from Google
    user_info = await get_google_user_info(token_data["access_token"])
    
    # Authenticate user with Google credentials
    result = await authenticate_google_user(db, user_info)
    
    return result 