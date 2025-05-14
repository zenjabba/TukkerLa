import cv2
import numpy as np
from pyzbar.pyzbar import decode
import requests
from typing import Optional, Dict, Any
from fastapi import UploadFile, HTTPException

from app.config import settings


async def scan_barcode_from_image(file: UploadFile) -> dict:
    """
    Scan a barcode from an uploaded image file.
    Returns the decoded barcode or raises an exception if no barcode is found.
    """
    # Read the image file
    content = await file.read()
    
    # Convert to OpenCV format
    nparr = np.frombuffer(content, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    
    # Improve image if needed
    img = cv2.GaussianBlur(img, (5, 5), 0)
    
    # Detect barcodes
    decoded_objects = decode(img)
    
    # If no barcode is found
    if not decoded_objects:
        raise HTTPException(status_code=400, detail="No barcode found in image")
    
    # Return the first barcode found
    barcode_obj = decoded_objects[0]
    return {
        "barcode": barcode_obj.data.decode('utf-8'),
        "barcode_type": barcode_obj.type,
    }


async def lookup_barcode_external(barcode: str) -> Optional[Dict[str, Any]]:
    """
    Look up a barcode using an external API if configured.
    Returns product information or None if not found/configured.
    """
    if not settings.BARCODE_API_URL or not settings.BARCODE_API_KEY:
        return None
        
    try:
        headers = {}
        if settings.BARCODE_API_KEY:
            headers["Authorization"] = f"Bearer {settings.BARCODE_API_KEY}"
            
        response = requests.get(
            f"{settings.BARCODE_API_URL}/{barcode}",
            headers=headers,
            timeout=5  # 5 second timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "product_name": data.get("name", f"Product {barcode}"),
                "default_expiry_days": data.get("shelf_life_days", 90),
                # Map external category to our category_id if possible
            }
    except Exception as e:
        print(f"Error looking up barcode: {e}")
    
    return None 