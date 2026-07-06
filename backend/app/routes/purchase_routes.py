from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.models.purchase import Purchase, PurchaseItem
from app.schemas.schemas import PurchaseCreate, PurchaseOut, PurchaseItemOut
from app.auth.auth import get_current_user
from app.services.stock_service import StockService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/purchases", tags=["Purchases"])

@router.get("", response_model=list[PurchaseOut])
def list_purchases(
    status: Optional[str] = None, supplier_id: Optional[int] = None,
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db), _: User = Depends(get_current_user),
):
    q = db.query(Purchase).options(joinedload(Purchase.supplier), joinedload(Purchase.items).joinedload(PurchaseItem.stock_item))
    if status: q = q.filter(Purchase.status == status)
    if supplier_id: q = q.filter(Purchase.supplier_id == supplier_id)
    ps = q.order_by(Purchase.purchase_date.desc()).offset(skip).limit(limit).all()
    result = []
    for p in ps:
        items = [PurchaseItemOut(id=i.id, stock_item_id=i.stock_item_id,
            stock_item_name=i.stock_item.name if i.stock_item else None,
            quantity=i.quantity, unit_cost=i.unit_cost, total_cost=i.total_cost) for i in p.items]
        result.append(PurchaseOut(id=p.id, supplier_id=p.supplier_id,
            supplier_name=p.supplier.name if p.supplier else None,
            purchase_date=p.purchase_date, invoice_number=p.invoice_number,
            total_cost=p.total_cost, payment_method=p.payment_method,
            status=p.status, notes=p.notes, created_by=p.created_by,
            items=items, created_at=p.created_at, updated_at=p.updated_at))
    return result

@router.get("/{purchase_id}", response_model=PurchaseOut)
def get_purchase(purchase_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    p = db.query(Purchase).options(
        joinedload(Purchase.supplier), joinedload(Purchase.items).joinedload(PurchaseItem.stock_item)
    ).filter(Purchase.id == purchase_id).first()
    if not p: raise HTTPException(404, "Purchase not found")
    items = [PurchaseItemOut(id=i.id, stock_item_id=i.stock_item_id,
        stock_item_name=i.stock_item.name if i.stock_item else None,
        quantity=i.quantity, unit_cost=i.unit_cost, total_cost=i.total_cost) for i in p.items]
    return PurchaseOut(id=p.id, supplier_id=p.supplier_id,
        supplier_name=p.supplier.name if p.supplier else None,
        purchase_date=p.purchase_date, invoice_number=p.invoice_number,
        total_cost=p.total_cost, payment_method=p.payment_method,
        status=p.status, notes=p.notes, created_by=p.created_by,
        items=items, created_at=p.created_at, updated_at=p.updated_at)

@router.post("", response_model=PurchaseOut, status_code=201)
def create_purchase(data: PurchaseCreate, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role.name not in ("admin", "financial"): raise HTTPException(403, "Insufficient permissions")
    total = sum(i.total_cost for i in data.items)
    purchase = Purchase(supplier_id=data.supplier_id, invoice_number=data.invoice_number,
        total_cost=total, payment_method=data.payment_method, status=data.status,
        notes=data.notes, created_by=current_user.id)
    db.add(purchase); db.flush()
    for item_data in data.items:
        pi = PurchaseItem(purchase_id=purchase.id, stock_item_id=item_data.stock_item_id,
            quantity=item_data.quantity, unit_cost=item_data.unit_cost, total_cost=item_data.total_cost)
        db.add(pi)
    db.commit()
    AuditService(db).log(action="create", entity_type="purchase", entity_id=purchase.id,
        user_id=current_user.id, username=current_user.username,
        ip_address=request.client.host if request.client else None,
        details=f"Purchase created, total R$ {total:.2f}")
    return get_purchase(purchase.id, db, current_user)

@router.post("/{purchase_id}/receive")
def receive_purchase(purchase_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role.name not in ("admin", "financial"): raise HTTPException(403, "Insufficient permissions")
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase: raise HTTPException(404, "Purchase not found")
    if purchase.status == "received": raise HTTPException(400, "Purchase already received")
    if purchase.status == "cancelled": raise HTTPException(400, "Purchase is cancelled")
    service = StockService(db)
    items = db.query(PurchaseItem).filter(PurchaseItem.purchase_id == purchase_id).all()
    for item in items:
        service.receive_stock(item.stock_item_id, item.quantity, item.unit_cost,
            reference_id=purchase_id, reference_type="purchase", performed_by=current_user.id)
    purchase.status = "received"
    db.commit()
    AuditService(db).log(action="receive", entity_type="purchase", entity_id=purchase.id,
        user_id=current_user.id, username=current_user.username,
        ip_address=request.client.host if request.client else None,
        details=f"Purchase #{purchase_id} received")
    return {"message": "Purchase received and stock updated", "purchase_id": purchase_id}

@router.post("/{purchase_id}/cancel")
def cancel_purchase(purchase_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role.name not in ("admin",): raise HTTPException(403, "Only admins can cancel purchases")
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase: raise HTTPException(404, "Purchase not found")
    purchase.status = "cancelled"; db.commit()
    return {"message": "Purchase cancelled"}
