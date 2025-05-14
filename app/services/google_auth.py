import requests
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models.users import User
from app.services.auth import create_access_token


async def exchange_code_for_token(code: str, redirect_uri: str) -> Dict[str, Any]:
    """
    Exchange the authorization code for a Google access token
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured"
        )
    
    token_url = settings.GOOGLE_TOKEN_URL
    
    payload = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    
    response = requests.post(token_url, data=payload)
    
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange code for token"
        )
    
    token_data = response.json()
    return token_data


async def get_google_user_info(access_token: str) -> Dict[str, Any]:
    """
    Get user info from Google using the access token
    """
    userinfo_url = settings.GOOGLE_USERINFO_URL
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(userinfo_url, headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Failed to get user info from Google"
        )
    
    user_info = response.json()
    return user_info


async def authenticate_google_user(db: Session, user_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Authenticate a user with Google credentials.
    If the user doesn't exist, create a new one.
    Return a JWT token.
    """
    # Check if user with Google ID exists
    google_id = user_info.get("sub")
    email = user_info.get("email")
    
    if not google_id or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user info from Google"
        )
    
    user = db.query(User).filter(User.google_id == google_id).first()
    
    # If not, check if user with same email exists
    if not user:
        user = db.query(User).filter(User.email == email).first()
        
        # If user exists but doesn't have google_id, update it
        if user:
            user.google_id = google_id
            user.auth_provider = "google"
            if user_info.get("picture"):
                user.picture = user_info.get("picture")
        # Otherwise, create a new user
        else:
            username = email.split("@")[0]
            
            # Make sure username is unique
            base_username = username
            count = 1
            while db.query(User).filter(User.username == username).first():
                username = f"{base_username}{count}"
                count += 1
            
            user = User(
                username=username,
                email=email,
                google_id=google_id,
                auth_provider="google",
                picture=user_info.get("picture")
            )
            db.add(user)
        
        db.commit()
        db.refresh(user)
    
    # Create JWT token
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.user_id}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin,
            "picture": user.picture
        }
    } 