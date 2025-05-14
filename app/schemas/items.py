from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Category schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase):
    category_id: int

    class Config:
        orm_mode = True


# Location schemas
class LocationBase(BaseModel):
    name: str
    description: Optional[str] = None


class LocationCreate(LocationBase):
    pass


class Location(LocationBase):
    location_id: int

    class Config:
        orm_mode = True


# Item schemas
class ItemBase(BaseModel):
    name: str
    barcode: Optional[str] = None
    category_id: Optional[int] = None
    location_id: Optional[int] = None
    quantity: int = 1
    stored_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    notes: Optional[str] = None
    storage_location: Optional[str] = "freezer"  # 'freezer', 'fridge', 'pantry'
    min_quantity: Optional[int] = 1
    unit: Optional[str] = None


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    barcode: Optional[str] = None
    category_id: Optional[int] = None
    location_id: Optional[int] = None
    quantity: Optional[int] = None
    stored_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    notes: Optional[str] = None
    storage_location: Optional[str] = None
    min_quantity: Optional[int] = None
    unit: Optional[str] = None


class Item(ItemBase):
    item_id: int
    added_by: int
    created_at: datetime
    updated_at: datetime
    category: Optional[Category] = None
    location: Optional[Location] = None

    class Config:
        orm_mode = True


class ItemDetail(Item):
    from app.schemas.images import Image
    images: List[Image] = []

    class Config:
        orm_mode = True 