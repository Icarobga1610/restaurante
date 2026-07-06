from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.product import Product
from app.schemas.schemas import ProductCreate, ProductUpdate, ProductOut
from app.auth.auth import get_current_user
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.get("", response_model=list[ProductOut])
def list_products(
    category: Optional[str] = None,
    active_only: bool = True,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Product)
    if active_only:
        query = query.filter(Product.is_active == True)
    if category:
        query = query.filter(Product.category == category)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    return query.order_by(Product.name).offset(skip).limit(limit).all()


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("", response_model=ProductOut, status_code=201)
def create_product(
    data: ProductCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.name not in ("admin",):
        raise HTTPException(status_code=403, detail="Only admins can create products")

    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)

    AuditService(db).log(
        action="create",
        entity_type="product",
        entity_id=product.id,
        user_id=current_user.id,
        username=current_user.username,
        ip_address=request.client.host if request.client else None,
        details=f"Created product {product.name}",
    )

    return product


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    data: ProductUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.name not in ("admin",):
        raise HTTPException(status_code=403, detail="Only admins can update products")

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    before = {"name": product.name, "price": product.price, "is_active": product.is_active}
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)

    AuditService(db).log(
        action="update",
        entity_type="product",
        entity_id=product.id,
        user_id=current_user.id,
        username=current_user.username,
        before_state=before,
        after_state={"name": product.name, "price": product.price, "is_active": product.is_active},
        ip_address=request.client.host if request.client else None,
        details=f"Updated product {product.name}",
    )

    return product


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.name not in ("admin",):
        raise HTTPException(status_code=403, detail="Only admins can delete products")

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.is_active = False
    db.commit()

    return {"message": "Product deactivated"}
