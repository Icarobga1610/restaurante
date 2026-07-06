from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.user import User
from app.models.product import Product
from app.models.product_recipe import ProductRecipe, ProductRecipeItem
from app.schemas.schemas import RecipeCreate, RecipeOut, RecipeItemOut
from app.auth.auth import get_current_user
from app.services.stock_service import StockService

router = APIRouter(prefix="/api/recipes", tags=["Recipes"])

@router.get("", response_model=list[RecipeOut])
def list_recipes(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    recipes = db.query(ProductRecipe).options(
        joinedload(ProductRecipe.product), joinedload(ProductRecipe.items).joinedload(ProductRecipeItem.stock_item)
    ).all()
    result = []
    for r in recipes:
        items = [RecipeItemOut(id=i.id, stock_item_id=i.stock_item_id,
            stock_item_name=i.stock_item.name if i.stock_item else None,
            quantity_required=i.quantity_required, unit_measure=i.unit_measure, cost=i.cost) for i in r.items]
        result.append(RecipeOut(id=r.id, product_id=r.product_id,
            product_name=r.product.name if r.product else None,
            total_cost=r.total_cost, estimated_margin=r.estimated_margin,
            version=r.version, notes=r.notes, items=items,
            created_at=r.created_at, updated_at=r.updated_at))
    return result

@router.get("/{recipe_id}", response_model=RecipeOut)
def get_recipe(recipe_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    r = db.query(ProductRecipe).options(
        joinedload(ProductRecipe.product), joinedload(ProductRecipe.items).joinedload(ProductRecipeItem.stock_item)
    ).filter(ProductRecipe.id == recipe_id).first()
    if not r: raise HTTPException(404, "Recipe not found")
    items = [RecipeItemOut(id=i.id, stock_item_id=i.stock_item_id,
        stock_item_name=i.stock_item.name if i.stock_item else None,
        quantity_required=i.quantity_required, unit_measure=i.unit_measure, cost=i.cost) for i in r.items]
    return RecipeOut(id=r.id, product_id=r.product_id,
        product_name=r.product.name if r.product else None,
        total_cost=r.total_cost, estimated_margin=r.estimated_margin,
        version=r.version, notes=r.notes, items=items,
        created_at=r.created_at, updated_at=r.updated_at)

@router.post("", response_model=RecipeOut, status_code=201)
def create_recipe(data: RecipeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role.name not in ("admin", "financial"): raise HTTPException(403, "Only admin/financial can manage recipes")
    existing = db.query(ProductRecipe).filter(ProductRecipe.product_id == data.product_id).first()
    if existing: raise HTTPException(400, "Product already has a recipe")
    recipe = ProductRecipe(product_id=data.product_id, notes=data.notes)
    db.add(recipe); db.flush()
    for item_data in data.items:
        ri = ProductRecipeItem(recipe_id=recipe.id, stock_item_id=item_data.stock_item_id,
            quantity_required=item_data.quantity_required, unit_measure=item_data.unit_measure, cost=item_data.cost)
        db.add(ri)
    db.commit()
    # Calculate cost
    StockService(db).calculate_recipe_cost(recipe.id)
    return get_recipe(recipe.id, db, current_user)

@router.put("/{recipe_id}", response_model=RecipeOut)
def update_recipe(recipe_id: int, data: RecipeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role.name not in ("admin", "financial"): raise HTTPException(403, "Only admin/financial can update recipes")
    recipe = db.query(ProductRecipe).filter(ProductRecipe.id == recipe_id).first()
    if not recipe: raise HTTPException(404, "Recipe not found")
    # Remove old items
    db.query(ProductRecipeItem).filter(ProductRecipeItem.recipe_id == recipe_id).delete()
    recipe.notes = data.notes; recipe.version += 1
    for item_data in data.items:
        ri = ProductRecipeItem(recipe_id=recipe.id, stock_item_id=item_data.stock_item_id,
            quantity_required=item_data.quantity_required, unit_measure=item_data.unit_measure, cost=item_data.cost)
        db.add(ri)
    db.commit()
    StockService(db).calculate_recipe_cost(recipe.id)
    return get_recipe(recipe.id, db, current_user)

@router.post("/{recipe_id}/recalculate")
def recalculate_cost(recipe_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    service = StockService(db)
    cost, margin = service.calculate_recipe_cost(recipe_id)
    return {"total_cost": cost, "estimated_margin": margin}
