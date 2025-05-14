from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models.items import Item
from app.schemas.items import (
    ItemCreate, 
    Item as ItemSchema, 
    ItemDetail,
    ItemUpdate
)
from app.services.auth import get_current_user
from app.models.users import User

router = APIRouter(prefix="/items", tags=["items"])


@router.post("/", response_model=ItemSchema)
def create_item(
    item: ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new freezer item."""
    db_item = Item(
        name=item.name,
        barcode=item.barcode,
        category_id=item.category_id,
        location_id=item.location_id,
        quantity=item.quantity,
        stored_date=item.stored_date or datetime.now(),
        expiry_date=item.expiry_date,
        notes=item.notes,
        added_by=current_user.user_id
    )
    
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    return db_item


@router.get("/", response_model=List[ItemSchema])
def get_items(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    location_id: Optional[int] = None,
    expiring_soon: bool = False,
    barcode: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all freezer items with optional filtering."""
    query = db.query(Item)
    
    # Apply filters
    if search:
        query = query.filter(Item.name.ilike(f"%{search}%"))
    if category_id:
        query = query.filter(Item.category_id == category_id)
    if location_id:
        query = query.filter(Item.location_id == location_id)
    if expiring_soon:
        soon = datetime.now() + timedelta(days=7)
        query = query.filter(Item.expiry_date <= soon)
    if barcode:
        query = query.filter(Item.barcode == barcode)
    
    # Apply pagination
    items = query.order_by(Item.expiry_date.asc()).offset(skip).limit(limit).all()
    
    return items


@router.get("/{item_id}", response_model=ItemDetail)
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific freezer item by ID."""
    item = db.query(Item).filter(Item.item_id == item_id).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    return item


@router.put("/{item_id}", response_model=ItemSchema)
def update_item(
    item_id: int,
    item_update: ItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a freezer item."""
    db_item = db.query(Item).filter(Item.item_id == item_id).first()
    
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    # Update fields if provided
    update_data = item_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
    
    db.commit()
    db.refresh(db_item)
    
    return db_item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a freezer item."""
    db_item = db.query(Item).filter(Item.item_id == item_id).first()
    
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    db.delete(db_item)
    db.commit()
    
    return None 