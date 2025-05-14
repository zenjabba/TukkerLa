from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class BarcodeProductBase(BaseModel):
    barcode: str
    product_name: str
    default_category_id: Optional[int] = None
    default_expiry_days: Optional[int] = None


class BarcodeProductCreate(BarcodeProductBase):
    pass


class BarcodeProduct(BarcodeProductBase):
    barcode_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class BarcodeResult(BaseModel):
    barcode: str
    barcode_type: Optional[str] = None
    product_name: Optional[str] = None
    default_category_id: Optional[int] = None
    default_expiry_days: Optional[int] = None
    source: str  # 'database', 'external', or 'unknown' 