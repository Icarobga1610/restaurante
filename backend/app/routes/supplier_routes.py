from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.models.supplier import Supplier
from app.schemas.schemas import SupplierCreate, SupplierUpdate, SupplierOut
from app.auth.auth import get_current_user

router = APIRouter(prefix="/api/suppliers", tags=["Suppliers"])

@router.get("", response_model=list[SupplierOut])
def list_suppliers(category: Optional[str] = None, status: Optional[str] = None, search: Optional[str] = None, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    q = db.query(Supplier)
    if category: q = q.filter(Supplier.category == category)
    if status: q = q.filter(Supplier.status == status)
    if search: q = q.filter(Supplier.name.ilike(f"%{search}%"))
    return q.order_by(Supplier.name).offset(skip).limit(limit).all()

@router.get("/{supplier_id}", response_model=SupplierOut)
def get_supplier(supplier_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    s = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not s: raise HTTPException(404, "Supplier not found")
    return s

@router.post("", response_model=SupplierOut, status_code=201)
def create_supplier(data: SupplierCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role.name not in ("admin",): raise HTTPException(403, "Only admins can create suppliers")
    supplier = Supplier(**data.model_dump()); db.add(supplier); db.commit(); db.refresh(supplier)
    return supplier

@router.put("/{supplier_id}", response_model=SupplierOut)
def update_supplier(supplier_id: int, data: SupplierUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role.name not in ("admin",): raise HTTPException(403, "Only admins can update")
    s = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not s: raise HTTPException(404, "Supplier not found")
    for k, v in data.model_dump(exclude_unset=True).items(): setattr(s, k, v)
    db.commit(); db.refresh(s); return s
