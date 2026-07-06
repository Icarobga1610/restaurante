from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from datetime import datetime
from app.utils import utcnow
from app.database import get_db
from app.models.user import User
from app.models.tab import Tab, TabItem
from app.models.restaurant_table import RestaurantTable
from app.models.order import Order
from app.schemas.schemas import TabCreate, TabOut, TabItemOut
from app.auth.auth import get_current_user
from app.services.audit_service import AuditService
from app.services.stock_service import StockService
from app.models.product import Product

router = APIRouter(prefix="/api/tabs", tags=["Tabs"])

@router.get("", response_model=list[TabOut])
def list_tabs(status: Optional[str] = None, table_id: Optional[int] = None,
              skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
              db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    q = db.query(Tab).options(joinedload(Tab.table), joinedload(Tab.client), joinedload(Tab.user), joinedload(Tab.items))
    if status: q = q.filter(Tab.status == status)
    if table_id: q = q.filter(Tab.table_id == table_id)
    tabs = q.order_by(Tab.opened_at.desc()).offset(skip).limit(limit).all()
    result = []
    for t in tabs:
        items = [TabItemOut(id=i.id, product_id=i.product_id, product_name=i.product_name,
            quantity=i.quantity, unit_price=i.unit_price, total=i.total, notes=i.notes, created_at=i.created_at) for i in t.items]
        result.append(TabOut(id=t.id, table_id=t.table_id, table_number=t.table.number if t.table else None,
            client_id=t.client_id, client_name=t.client.name if t.client else None,
            user_id=t.user_id, user_name=t.user.full_name if t.user else None,
            total=t.total, status=t.status, notes=t.notes,
            opened_at=t.opened_at, closed_at=t.closed_at, items=items,
            created_at=t.created_at, updated_at=t.updated_at))
    return result

@router.get("/{tab_id}", response_model=TabOut)
def get_tab(tab_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    t = db.query(Tab).options(joinedload(Tab.table), joinedload(Tab.client), joinedload(Tab.user), joinedload(Tab.items)).filter(Tab.id == tab_id).first()
    if not t: raise HTTPException(404, "Tab not found")
    items = [TabItemOut(id=i.id, product_id=i.product_id, product_name=i.product_name,
        quantity=i.quantity, unit_price=i.unit_price, total=i.total, notes=i.notes, created_at=i.created_at) for i in t.items]
    return TabOut(id=t.id, table_id=t.table_id, table_number=t.table.number if t.table else None,
        client_id=t.client_id, client_name=t.client.name if t.client else None,
        user_id=t.user_id, user_name=t.user.full_name if t.user else None,
        total=t.total, status=t.status, notes=t.notes,
        opened_at=t.opened_at, closed_at=t.closed_at, items=items,
        created_at=t.created_at, updated_at=t.updated_at)

@router.post("", response_model=TabOut, status_code=201)
def create_tab(data: TabCreate, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total = sum(i.total for i in data.items)
    tab = Tab(table_id=data.table_id, client_id=data.client_id, user_id=current_user.id, total=total, notes=data.notes)
    db.add(tab); db.flush()
    for item_data in data.items:
        ti = TabItem(tab_id=tab.id, product_id=item_data.product_id, product_name=item_data.product_name,
            quantity=item_data.quantity, unit_price=item_data.unit_price, total=item_data.total, notes=item_data.notes)
        db.add(ti)
    db.commit()
    AuditService(db).log(action="create", entity_type="tab", entity_id=tab.id,
        user_id=current_user.id, username=current_user.username,
        ip_address=request.client.host if request.client else None,
        details=f"Tab created, total R$ {total:.2f}")
    return get_tab(tab.id, db, current_user)

@router.post("/{tab_id}/add-item")
def add_tab_item(tab_id: int, data: dict, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    t = db.query(Tab).filter(Tab.id == tab_id).first()
    if not t: raise HTTPException(404, "Tab not found")
    if t.status != "open": raise HTTPException(400, "Tab is not open")
    ti = TabItem(tab_id=tab.id, product_id=data["product_id"], product_name=data["product_name"],
        quantity=data.get("quantity", 1), unit_price=data["unit_price"],
        total=data["quantity"] * data["unit_price"], notes=data.get("notes"))
    db.add(ti); t.total += ti.total; db.commit()
    return {"message": "Item added", "tab_id": tab_id}

@router.post("/{tab_id}/close")
def close_tab(
    tab_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    payment_method: str = "cash",
    send_to_monthly: bool = False,
):
    t = db.query(Tab).options(joinedload(Tab.items)).filter(Tab.id == tab_id).first()
    if not t: raise HTTPException(404, "Tab not found")
    if t.status != "open": raise HTTPException(400, "Tab is not open")

    if send_to_monthly and t.client_id:
        order = Order(client_id=t.client_id, user_id=current_user.id, tab_id=tab.id,
            table_id=t.table_id, status="confirmed", total=t.total)
        db.add(order); db.flush()
        for item in t.items:
            from app.models.order import OrderItem
            oi = OrderItem(order_id=order.id, product_id=item.product_id,
                product_name=item.product_name, quantity=item.quantity,
                unit_price=item.unit_price, total=item.total)
            db.add(oi)
        t.status = "sent_to_monthly"
        StockService(db).deduct_stock_for_order(order.id)
    else:
        t.status = "paid"

    t.closed_at = utcnow()
    if t.table_id:
        table = db.query(RestaurantTable).filter(RestaurantTable.id == t.table_id).first()
        if table: table.status = "free"; table.client_id = None
    db.commit()
    AuditService(db).log(action="close", entity_type="tab", entity_id=tab.id,
        user_id=current_user.id, username=current_user.username,
        ip_address=request.client.host if request.client else None,
        details=f"Tab closed, total R$ {t.total:.2f}, method: {payment_method}")
    return {"message": "Tab closed", "tab_id": tab_id, "total": t.total, "status": t.status}

@router.post("/{tab_id}/cancel")
def cancel_tab(tab_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    t = db.query(Tab).filter(Tab.id == tab_id).first()
    if not t: raise HTTPException(404, "Tab not found")
    t.status = "cancelled"; t.closed_at = utcnow()
    if t.table_id:
        table = db.query(RestaurantTable).filter(RestaurantTable.id == t.table_id).first()
        if table: table.status = "free"; table.client_id = None
    db.commit(); return {"message": "Tab cancelled"}
