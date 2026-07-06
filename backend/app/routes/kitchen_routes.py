from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from datetime import datetime
from app.utils import utcnow
from app.database import get_db
from app.models.user import User
from app.models.kitchen_order import KitchenOrder, KitchenOrderEvent
from app.models.order import Order, OrderItem
from app.schemas.schemas import KitchenOrderUpdate, KitchenOrderOut
from app.auth.auth import get_current_user

router = APIRouter(prefix="/api/kitchen", tags=["Kitchen"])

@router.get("/orders", response_model=list[KitchenOrderOut])
def list_kitchen_orders(
    status: Optional[str] = None, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db), _: User = Depends(get_current_user),
):
    q = db.query(KitchenOrder).options(joinedload(KitchenOrder.product), joinedload(KitchenOrder.assignee))
    if status: q = q.filter(KitchenOrder.status == status)
    else: q = q.filter(KitchenOrder.status.in_(["received", "in_preparation"]))
    kos = q.order_by(KitchenOrder.created_at.asc()).offset(skip).limit(limit).all()
    return [KitchenOrderOut(id=k.id, order_id=k.order_id, product_id=k.product_id,
        product_name=k.product_name, quantity=k.quantity, status=k.status,
        notes=k.notes, preparation_time_seconds=k.preparation_time_seconds,
        started_at=k.started_at, completed_at=k.completed_at,
        assigned_to=k.assigned_to, assignee_name=k.assignee.full_name if k.assignee else None,
        created_at=k.created_at, updated_at=k.updated_at) for k in kos]

@router.put("/orders/{order_id}/status")
def update_kitchen_status(order_id: int, data: KitchenOrderUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ko = db.query(KitchenOrder).filter(KitchenOrder.id == order_id).first()
    if not ko: raise HTTPException(404, "Kitchen order not found")

    from_status = ko.status
    to_status = data.status
    now = utcnow()

    if to_status == "in_preparation" and ko.status == "received":
        ko.started_at = now
    elif to_status == "ready" and ko.status == "in_preparation":
        ko.completed_at = now
        if ko.started_at:
            ko.preparation_time_seconds = int((now - ko.started_at).total_seconds())

    ko.status = to_status
    if data.notes: ko.notes = data.notes

    # Log event
    event = KitchenOrderEvent(kitchen_order_id=ko.id, from_status=from_status,
        to_status=to_status, performed_by=current_user.id, notes=data.notes)
    db.add(event)
    db.commit()

    # Also update the parent order status
    order = db.query(Order).filter(Order.id == ko.order_id).first()
    if order:
        # Check if all kitchen orders for this order are ready/delivered
        siblings = db.query(KitchenOrder).filter(KitchenOrder.order_id == ko.order_id).all()
        all_done = all(s.status in ("ready", "delivered") for s in siblings)
        any_in_prep = any(s.status == "in_preparation" for s in siblings)

        if all_done:
            order.status = "ready"
        elif any_in_prep:
            order.status = "in_preparation"
        elif to_status == "in_preparation":
            order.status = "in_preparation"
        db.commit()

    return {"message": f"Status updated: {from_status} → {to_status}", "prep_time_seconds": ko.preparation_time_seconds}

@router.post("/orders/generate/{order_id}")
def generate_kitchen_orders(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Generate kitchen orders from an order's items."""
    order = db.query(Order).options(joinedload(Order.items)).filter(Order.id == order_id).first()
    if not order: raise HTTPException(404, "Order not found")

    existing = db.query(KitchenOrder).filter(KitchenOrder.order_id == order_id).count()
    if existing > 0: raise HTTPException(400, "Kitchen orders already generated for this order")

    count = 0
    for item in order.items:
        ko = KitchenOrder(order_id=order.id, order_item_id=item.id,
            product_id=item.product_id, product_name=item.product_name,
            quantity=item.quantity, status="received")
        db.add(ko)
        count += 1

    order.status = "in_preparation"
    db.commit()
    return {"message": f"{count} kitchen orders generated", "order_id": order_id}
