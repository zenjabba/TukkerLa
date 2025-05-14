from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.images import Image
from app.models.items import Item
from app.schemas.images import Image as ImageSchema
from app.services.auth import get_current_user
from app.models.users import User
from app.services.image import save_image, delete_image

router = APIRouter(prefix="/images", tags=["images"])


@router.post("/{item_id}", response_model=ImageSchema)
async def upload_image(
    item_id: int,
    file: UploadFile = File(...),
    is_primary: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload an image for a freezer item."""
    # Verify item exists
    item = db.query(Item).filter(Item.item_id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    # Save image to disk
    image_info = await save_image(file)
    
    # If setting as primary, clear other primary flags
    if is_primary:
        db.query(Image).filter(
            Image.item_id == item_id,
            Image.is_primary == True
        ).update({"is_primary": False})
    
    # Create database record
    db_image = Image(
        item_id=item_id,
        image_path=image_info["relative_path"],
        is_primary=is_primary
    )
    
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    
    return db_image


@router.get("/{item_id}", response_model=List[ImageSchema])
def get_item_images(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all images for a specific freezer item."""
    # Verify item exists
    item = db.query(Item).filter(Item.item_id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    # Get images
    images = db.query(Image).filter(Image.item_id == item_id).all()
    
    return images


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an image."""
    # Get image
    db_image = db.query(Image).filter(Image.image_id == image_id).first()
    
    if not db_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Delete from disk
    success = await delete_image(db_image.image_path)
    
    if not success:
        # Continue even if file deletion fails (might have already been removed)
        pass
    
    # Delete from database
    db.delete(db_image)
    db.commit()
    
    return None


@router.put("/{image_id}/primary", response_model=ImageSchema)
def set_primary_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set an image as the primary image for its item."""
    # Get image
    db_image = db.query(Image).filter(Image.image_id == image_id).first()
    
    if not db_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Clear other primary flags for this item
    db.query(Image).filter(
        Image.item_id == db_image.item_id,
        Image.is_primary == True
    ).update({"is_primary": False})
    
    # Set this image as primary
    db_image.is_primary = True
    db.commit()
    db.refresh(db_image)
    
    return db_image 