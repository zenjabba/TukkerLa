from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from decimal import Decimal


class RecipeIngredientBase(BaseModel):
    name: str
    quantity: Union[Decimal, float]
    unit: Optional[str] = None
    item_id: Optional[int] = None


class RecipeIngredientCreate(RecipeIngredientBase):
    pass


class RecipeIngredient(RecipeIngredientBase):
    id: int
    recipe_id: int

    class Config:
        orm_mode = True


class RecipeImageBase(BaseModel):
    image_path: str
    is_primary: bool = False


class RecipeImageCreate(RecipeImageBase):
    pass


class RecipeImage(RecipeImageBase):
    image_id: int
    recipe_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class RecipePreferenceBase(BaseModel):
    liked: Optional[bool] = None
    notes: Optional[str] = None


class RecipePreferenceCreate(RecipePreferenceBase):
    user_id: int
    recipe_id: int


class RecipePreference(RecipePreferenceBase):
    id: int
    user_id: int
    recipe_id: int

    class Config:
        orm_mode = True


class RecipeBase(BaseModel):
    name: str
    instructions: Optional[str] = None
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    servings: Optional[int] = None
    rating: Optional[int] = None
    notes: Optional[str] = None


class RecipeCreate(RecipeBase):
    ingredients: List[RecipeIngredientCreate] = []


class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    instructions: Optional[str] = None
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    servings: Optional[int] = None
    rating: Optional[int] = None
    notes: Optional[str] = None


class Recipe(RecipeBase):
    recipe_id: int
    created_by: int
    created_at: datetime
    ingredients: List[RecipeIngredient] = []
    images: List[RecipeImage] = []

    class Config:
        orm_mode = True


class RecipeDetail(Recipe):
    preferences: List[RecipePreference] = []

    class Config:
        orm_mode = True


class MealPlanBase(BaseModel):
    date: date
    meal_type: str  # breakfast, lunch, dinner, snack
    recipe_id: Optional[int] = None
    notes: Optional[str] = None


class MealPlanCreate(MealPlanBase):
    pass


class MealPlanUpdate(BaseModel):
    date: Optional[date] = None
    meal_type: Optional[str] = None
    recipe_id: Optional[int] = None
    notes: Optional[str] = None


class MealPlan(MealPlanBase):
    plan_id: int
    created_by: int
    recipe: Optional[Recipe] = None

    class Config:
        orm_mode = True


class ShoppingListItemBase(BaseModel):
    name: str
    quantity: Optional[Union[Decimal, float]] = None
    unit: Optional[str] = None
    item_id: Optional[int] = None
    checked: bool = False


class ShoppingListItemCreate(ShoppingListItemBase):
    pass


class ShoppingListItemUpdate(BaseModel):
    name: Optional[str] = None
    quantity: Optional[Union[Decimal, float]] = None
    unit: Optional[str] = None
    checked: Optional[bool] = None


class ShoppingListItem(ShoppingListItemBase):
    id: int
    added_by: int
    created_at: datetime

    class Config:
        orm_mode = True


class CookRecipe(BaseModel):
    servings: Optional[int] = None  # Override recipe servings if provided 