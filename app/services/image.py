import os
import uuid
from fastapi import UploadFile, HTTPException
from typing import Dict, Any
from PIL import Image as PILImage
import io

from app.config import settings


async def save_image(file: UploadFile, directory: str = None) -> Dict[str, Any]:
    """
    Save an uploaded image to disk with a unique filename.
    Returns the relative path to the saved image.
    
    Args:
        file (UploadFile): The uploaded file object
        directory (str, optional): Subdirectory to save in. Defaults to None.
    
    Returns:
        Dict[str, Any]: Information about the saved image
    """
    # Validate file is an image
    content_type = file.content_type
    if not content_type or not content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File is not a valid image")
    
    # Determine upload path
    upload_dir = settings.UPLOAD_DIRECTORY
    if directory:
        upload_dir = os.path.join(upload_dir, directory)
    
    # Create directory if it doesn't exist
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Create relative path for storage in DB
    rel_path = os.path.join("images", directory or "", unique_filename)
    
    # Reset file cursor
    await file.seek(0)
    
    # Optimize and save image
    try:
        # Read image data
        content = await file.read()
        
        # Process with PIL
        img = PILImage.open(io.BytesIO(content))
        
        # Resize if necessary (e.g., if it's too large)
        max_size = (1200, 1200)  # Maximum dimensions
        if img.width > max_size[0] or img.height > max_size[1]:
            img.thumbnail(max_size, PILImage.LANCZOS)
        
        # Save optimized image
        img.save(file_path, optimize=True, quality=85)
        
        # Get image info
        return {
            "filename": unique_filename,
            "content_type": content_type,
            "size": os.path.getsize(file_path),
            "path": file_path,
            "relative_path": rel_path,
            "width": img.width,
            "height": img.height
        }
        
    except Exception as e:
        # Clean up if there was an error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error saving image: {str(e)}")


async def delete_image(image_path: str) -> bool:
    """
    Delete an image file from disk.
    
    Args:
        image_path (str): The path to the image file
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Calculate the full path
        if not image_path.startswith("/"):
            # If it's a relative path, join with upload directory
            full_path = os.path.join(settings.UPLOAD_DIRECTORY, image_path)
        else:
            # If it's an absolute path, use it directly
            full_path = image_path
            
        # Check if file exists
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False
    except Exception as e:
        print(f"Error deleting image: {e}")
        return False 