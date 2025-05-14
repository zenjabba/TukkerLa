from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.items import Location
from app.schemas.items import (
    LocationCreate, 
    Location as LocationSchema
)
from app.services.auth import get_current_user
from app.models.users import User

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("/", response_model=List[LocationSchema])
def get_locations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all freezer locations."""
    locations = db.query(Location).offset(skip).limit(limit).all()
    return locations


@router.post("/", response_model=LocationSchema)
def create_location(
    location: LocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new freezer location."""
    db_location = db.query(Location).filter(Location.name == location.name).first()
    if db_location:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Location already exists"
        )
    
    db_location = Location(**location.dict())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    
    return db_location


@router.get("/{location_id}", response_model=LocationSchema)
def get_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific freezer location by ID."""
    db_location = db.query(Location).filter(Location.location_id == location_id).first()
    if not db_location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    return db_location


@router.put("/{location_id}", response_model=LocationSchema)
def update_location(
    location_id: int,
    location: LocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a freezer location."""
    db_location = db.query(Location).filter(Location.location_id == location_id).first()
    if not db_location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    # Check if new name conflicts with existing location
    if location.name != db_location.name:
        existing = db.query(Location).filter(Location.name == location.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Location name already exists"
            )
    
    # Update fields
    db_location.name = location.name
    db_location.description = location.description
    
    db.commit()
    db.refresh(db_location)
    
    return db_location


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a freezer location."""
    db_location = db.query(Location).filter(Location.location_id == location_id).first()
    if not db_location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    # Check if location is in use
    from app.models.items import Item
    items_with_location = db.query(Item).filter(Item.location_id == location_id).count()
    if items_with_location > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete location as it's used by {items_with_location} items"
        )
    
    db.delete(db_location)
    db.commit()
    
    return None 