from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from datetime import date
from app.database import get_db
from app.models.user import User
from app.models.stock_item import StockItem
from app.models.stock_movement import StockMovement
from app.schemas.schemas import StockItemCreate, StockItemUpdate, StockItemOut, StockMovementCreate, StockMovementOut
from app.auth.auth import get_current_user
from app.services.stock_service import StockService
from app.services.audit_service import AuditService
from app.utils import entity_code

router = APIRouter(prefix="/api/stock", tags=["Stock"])

@router.get("/items", response_model=list[StockItemOut])
def list_stock_items(
    category: Optional[str] = None, low_stock: bool = False,
    search: Optional[str] = None, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db), _: User = Depends(get_current_user),
):
    q = db.query(StockItem).options(joinedload(StockItem.supplier))
    if category: q = q.filter(StockItem.category == category)
    if low_stock: q = q.filter(StockItem.current_quantity <= StockItem.minimum_stock, StockItem.minimum_stock > 0)
    if search: q = q.filter(or_(StockItem.name.ilike(f"%{search}%"), StockItem.code.ilike(f"%{search}%")))
    items = q.order_by(StockItem.name).offset(skip).limit(limit).all()
    return [StockItemOut(id=i.id, code=i.code, name=i.name, category=i.category, unit_measure=i.unit_measure,
        current_quantity=i.current_quantity, minimum_stock=i.minimum_stock, unit_cost=i.unit_cost,
        average_cost=i.average_cost, supplier_id=i.supplier_id,
        supplier_name=i.supplier.name if i.supplier else None,
        expiry_date=i.expiry_date, status=i.status, notes=i.notes,
        created_at=i.created_at, updated_at=i.updated_at) for i in items]

@router.get("/items/{item_id}", response_model=StockItemOut)
def get_stock_item(item_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    i = db.query(StockItem).options(joinedload(StockItem.supplier)).filter(StockItem.id == item_id).first()
    if not i: raise HTTPException(404, "Stock item not found")
    return StockItemOut(id=i.id, code=i.code, name=i.name, category=i.category, unit_measure=i.unit_measure,
        current_quantity=i.current_quantity, minimum_stock=i.minimum_stock, unit_cost=i.unit_cost,
        average_cost=i.average_cost, supplier_id=i.supplier_id,
        supplier_name=i.supplier.name if i.supplier else None,
        expiry_date=i.expiry_date, status=i.status, notes=i.notes,
        created_at=i.created_at, updated_at=i.updated_at)

@router.post("/items", response_model=StockItemOut, status_code=201)
def create_stock_item(data: StockItemCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role.name not in ("admin", "financial"): raise HTTPException(403, "Only admin/financial can manage stock")
    item = StockItem(**data.model_dump()); db.add(item); db.commit(); db.refresh(item)
    if not item.code:
        item.code = entity_code("ING", item.id)
        db.commit()
        db.refresh(item)
    return item

@router.put("/items/{item_id}", response_model=StockItemOut)
def update_stock_item(item_id: int, data: StockItemUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role.name not in ("admin", "financial"): raise HTTPException(403, "Only admin/financial can manage stock")
    i = db.query(StockItem).filter(StockItem.id == item_id).first()
    if not i: raise HTTPException(404, "Stock item not found")
    for k, v in data.model_dump(exclude_unset=True).items(): setattr(i, k, v)
    db.commit(); db.refresh(i); return i

@router.get("/movements", response_model=list[StockMovementOut])
def list_movements(
    item_id: Optional[int] = None, movement_type: Optional[str] = None,
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db), _: User = Depends(get_current_user),
):
    q = db.query(StockMovement).options(joinedload(StockMovement.stock_item), joinedload(StockMovement.performer))
    if item_id: q = q.filter(StockMovement.stock_item_id == item_id)
    if movement_type: q = q.filter(StockMovement.movement_type == movement_type)
    ms = q.order_by(StockMovement.created_at.desc()).offset(skip).limit(limit).all()
    return [StockMovementOut(id=m.id, stock_item_id=m.stock_item_id,
        stock_item_name=m.stock_item.name if m.stock_item else None,
        movement_type=m.movement_type, quantity=m.quantity, unit_cost=m.unit_cost,
        total_cost=m.total_cost, reference_id=m.reference_id, reference_type=m.reference_type,
        notes=m.notes, performed_by=m.performed_by,
        performer_name=m.performer.full_name if m.performer else None,
        created_at=m.created_at) for m in ms]

@router.post("/movements", response_model=StockMovementOut, status_code=201)
def create_movement(data: StockMovementCreate, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role.name not in ("admin", "financial"): raise HTTPException(403, "Insufficient permissions")
    service = StockService(db)
    if data.movement_type in ("entrada_compra",):
        item = service.receive_stock(data.stock_item_id, abs(data.quantity), data.unit_cost or 0, data.reference_id, data.reference_type, data.notes, current_user.id)
    elif data.movement_type in ("ajuste_manual",):
        stock = db.query(StockItem).filter(StockItem.id == data.stock_item_id).first()
        if stock:
            service.adjust_stock(data.stock_item_id, stock.current_quantity + data.quantity, data.movement_type, data.notes, current_user.id)
    else:
        stock = db.query(StockItem).filter(StockItem.id == data.stock_item_id).first()
        if stock:
            stock.current_quantity += data.quantity
            m = StockMovement(stock_item_id=data.stock_item_id, movement_type=data.movement_type,
                quantity=data.quantity, unit_cost=data.unit_cost,
                total_cost=abs(data.quantity) * (data.unit_cost or stock.average_cost or stock.unit_cost),
                reference_id=data.reference_id, reference_type=data.reference_type,
                notes=data.notes, performed_by=current_user.id)
            db.add(m); db.commit()
    db.commit()
    return {"message": "Movement registered", "stock_item_id": data.stock_item_id}

@router.get("/alerts/low-stock")
def get_low_stock_alerts(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    service = StockService(db)
    items = service.get_low_stock_items()
    return [{"id": i.id, "name": i.name, "current": i.current_quantity, "minimum": i.minimum_stock, "unit": i.unit_measure} for i in items]

@router.get("/alerts/expiring")
def get_expiring_alerts(days: int = Query(15), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    service = StockService(db)
    items = service.get_expiring_items(days)
    return [{"id": i.id, "name": i.name, "expiry_date": str(i.expiry_date), "quantity": i.current_quantity} for i in items]
