from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from decimal import Decimal

from app.models.recipes import Recipe, RecipeIngredient
from app.models.items import Item
from app.schemas.recipes import CookRecipe


async def cook_recipe(
    db: Session, 
    recipe_id: int, 
    cook_data: CookRecipe, 
    user_id: int
) -> Dict[str, Any]:
    """
    Cook a recipe and deduct ingredients from inventory.
    Returns a dictionary of results with items changed and any warnings.
    """
    # Get the recipe
    recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
        
    # Get the ingredients
    ingredients = db.query(RecipeIngredient).filter(
        RecipeIngredient.recipe_id == recipe_id
    ).all()
    
    if not ingredients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recipe has no ingredients to deduct"
        )
    
    # Determine servings multiplier
    servings = cook_data.servings or recipe.servings or 1
    multiplier = Decimal(servings) / Decimal(recipe.servings or 1)
    
    # Track results
    results = {
        "success": True,
        "deducted_items": [],
        "missing_items": [],
        "low_stock_warnings": []
    }
    
    # Process each ingredient
    for ingredient in ingredients:
        if not ingredient.item_id:
            # Skip ingredients not linked to inventory items
            results["missing_items"].append({
                "name": ingredient.name,
                "quantity": float(ingredient.quantity * multiplier),
                "unit": ingredient.unit
            })
            continue
            
        # Get the inventory item
        item = db.query(Item).filter(Item.item_id == ingredient.item_id).first()
        if not item:
            results["missing_items"].append({
                "name": ingredient.name,
                "quantity": float(ingredient.quantity * multiplier),
                "unit": ingredient.unit
            })
            continue
            
        # Calculate amount to deduct
        to_deduct = ingredient.quantity * multiplier
        
        # Check if enough inventory
        if item.quantity < to_deduct:
            results["missing_items"].append({
                "name": item.name,
                "available": item.quantity,
                "needed": float(to_deduct),
                "unit": item.unit or ingredient.unit
            })
            continue
            
        # Deduct from inventory
        item.quantity -= int(to_deduct)
        db.add(item)
        
        # Add to deducted items
        results["deducted_items"].append({
            "name": item.name,
            "deducted": float(to_deduct),
            "remaining": item.quantity,
            "unit": item.unit or ingredient.unit
        })
        
        # Check if now below minimum quantity
        if item.quantity <= item.min_quantity:
            results["low_stock_warnings"].append({
                "name": item.name,
                "current": item.quantity,
                "minimum": item.min_quantity,
                "unit": item.unit
            })
    
    # Commit changes if any items were deducted
    if results["deducted_items"]:
        db.commit()
    else:
        results["success"] = False
        
    return results


async def generate_shopping_list(
    db: Session,
    recipes: Optional[List[int]] = None,
    include_low_stock: bool = True,
    user_id: int = None
) -> List[Dict[str, Any]]:
    """
    Generate a shopping list based on:
    1. Low stock items (optional)
    2. Missing ingredients for specified recipes
    
    Returns a list of items to add to shopping list
    """
    shopping_items = []
    
    # Add low stock items
    if include_low_stock:
        low_stock = db.query(Item).filter(
            Item.quantity <= Item.min_quantity
        ).all()
        
        for item in low_stock:
            amount_needed = item.min_quantity - item.quantity
            if amount_needed <= 0:
                amount_needed = 1
                
            shopping_items.append({
                "name": item.name,
                "quantity": amount_needed,
                "unit": item.unit,
                "item_id": item.item_id,
                "source": "low_stock"
            })
    
    # Add recipe ingredients
    if recipes:
        for recipe_id in recipes:
            recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
            if not recipe:
                continue
                
            ingredients = db.query(RecipeIngredient).filter(
                RecipeIngredient.recipe_id == recipe_id
            ).all()
            
            for ingredient in ingredients:
                # Check if we already have this in inventory
                if ingredient.item_id:
                    item = db.query(Item).filter(Item.item_id == ingredient.item_id).first()
                    if item and item.quantity >= ingredient.quantity:
                        # We have enough, skip
                        continue
                        
                    if item:
                        # We have some but not enough
                        needed = ingredient.quantity - item.quantity
                        shopping_items.append({
                            "name": ingredient.name,
                            "quantity": float(needed),
                            "unit": ingredient.unit or item.unit,
                            "item_id": ingredient.item_id,
                            "source": f"recipe:{recipe.name}"
                        })
                        continue
                        
                # Add the ingredient
                shopping_items.append({
                    "name": ingredient.name,
                    "quantity": float(ingredient.quantity),
                    "unit": ingredient.unit,
                    "item_id": ingredient.item_id,
                    "source": f"recipe:{recipe.name}"
                })
    
    return shopping_items 