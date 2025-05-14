from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.recipes import Recipe, RecipeIngredient, RecipeImage, RecipePreference
from app.schemas.recipes import (
    RecipeCreate,
    Recipe as RecipeSchema,
    RecipeDetail,
    RecipeUpdate,
    RecipeIngredientCreate,
    RecipeIngredient as RecipeIngredientSchema,
    CookRecipe
)
from app.services.auth import get_current_user
from app.models.users import User
from app.services.image import save_image
from app.services.recipe import cook_recipe

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.post("/", response_model=RecipeSchema)
async def create_recipe(
    recipe: RecipeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new recipe with ingredients."""
    # Create recipe
    db_recipe = Recipe(
        name=recipe.name,
        instructions=recipe.instructions,
        prep_time=recipe.prep_time,
        cook_time=recipe.cook_time,
        servings=recipe.servings,
        rating=recipe.rating,
        notes=recipe.notes,
        created_by=current_user.user_id
    )
    
    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)
    
    # Add ingredients
    for ingredient in recipe.ingredients:
        db_ingredient = RecipeIngredient(
            recipe_id=db_recipe.recipe_id,
            name=ingredient.name,
            quantity=ingredient.quantity,
            unit=ingredient.unit,
            item_id=ingredient.item_id
        )
        db.add(db_ingredient)
    
    db.commit()
    db.refresh(db_recipe)
    
    return db_recipe


@router.get("/", response_model=List[RecipeSchema])
async def get_recipes(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all recipes with optional filtering."""
    query = db.query(Recipe)
    
    # Apply filters
    if search:
        query = query.filter(Recipe.name.ilike(f"%{search}%"))
    
    recipes = query.offset(skip).limit(limit).all()
    return recipes


@router.get("/{recipe_id}", response_model=RecipeDetail)
async def get_recipe(
    recipe_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific recipe by ID."""
    recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    
    return recipe


@router.put("/{recipe_id}", response_model=RecipeSchema)
async def update_recipe(
    recipe_id: int,
    recipe_update: RecipeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a recipe."""
    db_recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
    
    if not db_recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    
    # Update fields if provided
    update_data = recipe_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_recipe, key, value)
    
    db.commit()
    db.refresh(db_recipe)
    
    return db_recipe


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a recipe."""
    db_recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
    
    if not db_recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    
    db.delete(db_recipe)
    db.commit()
    
    return None


@router.post("/{recipe_id}/images", response_model=RecipeImage)
async def upload_recipe_image(
    recipe_id: int,
    file: UploadFile = File(...),
    is_primary: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload an image for a recipe."""
    # Verify recipe exists
    recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    
    # Save image to disk
    image_info = await save_image(file, directory="recipes")
    
    # If setting as primary, clear other primary flags
    if is_primary:
        db.query(RecipeImage).filter(
            RecipeImage.recipe_id == recipe_id,
            RecipeImage.is_primary == True
        ).update({"is_primary": False})
    
    # Create database record
    db_image = RecipeImage(
        recipe_id=recipe_id,
        image_path=image_info["relative_path"],
        is_primary=is_primary
    )
    
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    
    return db_image


@router.post("/{recipe_id}/ingredients", response_model=RecipeIngredientSchema)
async def add_recipe_ingredient(
    recipe_id: int,
    ingredient: RecipeIngredientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add an ingredient to a recipe."""
    # Verify recipe exists
    recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    
    # Create ingredient
    db_ingredient = RecipeIngredient(
        recipe_id=recipe_id,
        name=ingredient.name,
        quantity=ingredient.quantity,
        unit=ingredient.unit,
        item_id=ingredient.item_id
    )
    
    db.add(db_ingredient)
    db.commit()
    db.refresh(db_ingredient)
    
    return db_ingredient


@router.post("/{recipe_id}/cook")
async def cook_recipe_endpoint(
    recipe_id: int,
    cook_data: CookRecipe,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cook a recipe, deducting ingredients from inventory.
    Returns results of the cooking operation.
    """
    result = await cook_recipe(
        db=db,
        recipe_id=recipe_id,
        cook_data=cook_data,
        user_id=current_user.user_id
    )
    
    return result


@router.post("/{recipe_id}/preference")
async def set_recipe_preference(
    recipe_id: int,
    liked: bool = Form(...),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set preference (like/dislike) for a recipe."""
    # Verify recipe exists
    recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    
    # Check if preference already exists
    preference = db.query(RecipePreference).filter(
        RecipePreference.recipe_id == recipe_id,
        RecipePreference.user_id == current_user.user_id
    ).first()
    
    if preference:
        # Update existing preference
        preference.liked = liked
        preference.notes = notes
    else:
        # Create new preference
        preference = RecipePreference(
            recipe_id=recipe_id,
            user_id=current_user.user_id,
            liked=liked,
            notes=notes
        )
        db.add(preference)
    
    db.commit()
    db.refresh(preference)
    
    return {"status": "success", "preference": preference} 