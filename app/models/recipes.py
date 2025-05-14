from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean, SmallInteger, Date, Numeric
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import relationship
from app.database import Base


class Recipe(Base):
    __tablename__ = "recipes"
    
    recipe_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    instructions = Column(Text)
    prep_time = Column(Integer)  # In minutes
    cook_time = Column(Integer)  # In minutes
    servings = Column(Integer)
    rating = Column(SmallInteger)  # 1-5 stars
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.user_id"))
    created_at = Column(TIMESTAMP(timezone=True), 
                         server_default=text('now()'), 
                         nullable=False)
    
    # Relationships
    created_by_user = relationship("User")
    ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")
    images = relationship("RecipeImage", back_populates="recipe", cascade="all, delete-orphan")
    preferences = relationship("RecipePreference", back_populates="recipe", cascade="all, delete-orphan")
    meal_plans = relationship("MealPlan", back_populates="recipe")


class RecipeImage(Base):
    __tablename__ = "recipe_images"
    
    image_id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.recipe_id", ondelete="CASCADE"))
    image_path = Column(String, nullable=False)
    is_primary = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), 
                         server_default=text('now()'), 
                         nullable=False)
    
    # Relationships
    recipe = relationship("Recipe", back_populates="images")


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.recipe_id", ondelete="CASCADE"))
    name = Column(String(100), nullable=False)
    quantity = Column(Numeric, nullable=False)
    unit = Column(String(20))
    item_id = Column(Integer, ForeignKey("items.item_id", ondelete="SET NULL"))
    
    # Relationships
    recipe = relationship("Recipe", back_populates="ingredients")
    item = relationship("Item")


class RecipePreference(Base):
    __tablename__ = "recipe_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.recipe_id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"))
    liked = Column(Boolean)
    notes = Column(Text)
    
    # Relationships
    recipe = relationship("Recipe", back_populates="preferences")
    user = relationship("User")


class MealPlan(Base):
    __tablename__ = "meal_plans"
    
    plan_id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    meal_type = Column(String(20), nullable=False)  # breakfast, lunch, dinner, snack
    recipe_id = Column(Integer, ForeignKey("recipes.recipe_id"))
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.user_id"))
    
    # Relationships
    recipe = relationship("Recipe", back_populates="meal_plans")
    created_by_user = relationship("User")


class ShoppingListItem(Base):
    __tablename__ = "shopping_list"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    quantity = Column(Numeric)
    unit = Column(String(20))
    item_id = Column(Integer, ForeignKey("items.item_id", ondelete="SET NULL"))
    added_by = Column(Integer, ForeignKey("users.user_id"))
    checked = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), 
                         server_default=text('now()'), 
                         nullable=False)
    
    # Relationships
    item = relationship("Item")
    added_by_user = relationship("User") 