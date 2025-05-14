from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ImageBase(BaseModel):
    image_path: str
    is_primary: bool = False


class ImageCreate(ImageBase):
    pass


class Image(ImageBase):
    image_id: int
    item_id: int
    created_at: datetime

    class Config:
        orm_mode = True 