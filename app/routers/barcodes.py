from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.barcode_products import BarcodeProduct
from app.schemas.barcodes import (
    BarcodeResult,
    BarcodeProduct as BarcodeProductSchema,
    BarcodeProductCreate
)
from app.services.auth import get_current_user
from app.models.users import User
from app.services.barcode import scan_barcode_from_image, lookup_barcode_external

router = APIRouter(prefix="/barcodes", tags=["barcodes"])


@router.post("/scan", response_model=BarcodeResult)
async def scan_barcode(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Scan a barcode from an uploaded image.
    Returns the decoded barcode and any product information if available.
    """
    # Scan the barcode from the image
    try:
        barcode_data = await scan_barcode_from_image(file)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process barcode: {str(e)}"
        )
    
    barcode = barcode_data["barcode"]
    barcode_type = barcode_data["barcode_type"]
    
    # Check if barcode exists in database
    db_product = db.query(BarcodeProduct).filter(
        BarcodeProduct.barcode == barcode
    ).first()
    
    if db_product:
        # Return product info from database
        return {
            "barcode": barcode,
            "barcode_type": barcode_type,
            "product_name": db_product.product_name,
            "default_category_id": db_product.default_category_id,
            "default_expiry_days": db_product.default_expiry_days,
            "source": "database"
        }
    
    # If not in database, try external lookup
    product_info = await lookup_barcode_external(barcode)
    if product_info:
        # Save to database for future lookups
        new_product = BarcodeProduct(
            barcode=barcode,
            product_name=product_info["product_name"],
            default_category_id=product_info.get("default_category_id"),
            default_expiry_days=product_info.get("default_expiry_days", 90)
        )
        
        db.add(new_product)
        db.commit()
        
        return {
            "barcode": barcode,
            "barcode_type": barcode_type,
            "product_name": product_info["product_name"],
            "default_category_id": product_info.get("default_category_id"),
            "default_expiry_days": product_info.get("default_expiry_days"),
            "source": "external"
        }
    
    # If not found anywhere
    return {
        "barcode": barcode,
        "barcode_type": barcode_type,
        "product_name": None,
        "default_category_id": None,
        "default_expiry_days": None,
        "source": "unknown"
    }


@router.post("/products", response_model=BarcodeProductSchema)
def create_barcode_product(
    product: BarcodeProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create or update a barcode product mapping in the database.
    """
    # Check if barcode already exists
    db_product = db.query(BarcodeProduct).filter(
        BarcodeProduct.barcode == product.barcode
    ).first()
    
    if db_product:
        # Update existing product
        for key, value in product.dict().items():
            setattr(db_product, key, value)
    else:
        # Create new product
        db_product = BarcodeProduct(**product.dict())
        db.add(db_product)
    
    db.commit()
    db.refresh(db_product)
    
    return db_product


@router.get("/products/{barcode}", response_model=BarcodeProductSchema)
def get_barcode_product(
    barcode: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get product information for a barcode from the database.
    """
    db_product = db.query(BarcodeProduct).filter(
        BarcodeProduct.barcode == barcode
    ).first()
    
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Barcode not found"
        )
    
    return db_product 