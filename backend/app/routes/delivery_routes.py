from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.order import Order, OrderItem
from app.models.delivery import DeliveryAddress, DeliveryEvent
from app.schemas.schemas import DeliveryAddressCreate, DeliveryAddressOut, DeliveryEventOut
from app.auth.auth import get_current_user
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/delivery", tags=["Delivery"])


# ── Addresses ──────────────────────────────────────────────────

@router.get("/addresses", response_model=list[DeliveryAddressOut])
def list_addresses(
    client_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(DeliveryAddress)
    if client_id:
        query = query.filter(DeliveryAddress.client_id == client_id)
    return query.order_by(DeliveryAddress.is_default.desc()).all()


@router.post("/addresses", response_model=DeliveryAddressOut, status_code=201)
def create_address(
    data: DeliveryAddressCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.is_default:
        db.query(DeliveryAddress).filter(
            DeliveryAddress.client_id == data.client_id
        ).update({"is_default": False})
    address = DeliveryAddress(**data.model_dump())
    db.add(address)
    db.commit()
    db.refresh(address)

    AuditService(db).log(
        action="create", entity_type="delivery_address", entity_id=address.id,
        user_id=current_user.id, username=current_user.username,
        details=f"Endereço de entrega criado para cliente #{data.client_id}",
    )
    return address


@router.delete("/addresses/{address_id}", status_code=204)
def delete_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    address = db.query(DeliveryAddress).filter(DeliveryAddress.id == address_id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Endereço não encontrado")
    db.delete(address)
    db.commit()

    AuditService(db).log(
        action="delete", entity_type="delivery_address", entity_id=address_id,
        user_id=current_user.id, username=current_user.username,
        details="Endereço de entrega removido",
    )


# ── Delivery Orders ────────────────────────────────────────────

@router.get("/orders", response_model=list[dict])
def list_delivery_orders(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Order).options(
        joinedload(Order.client), joinedload(Order.items),
        joinedload(Order.delivery_address),
    ).filter(
        Order.order_type.in_(["delivery", "retirada"])
    )
    if status:
        query = query.filter(Order.delivery_status == status)
    orders = query.order_by(Order.created_at.desc()).all()

    result = []
    for o in orders:
        result.append({
            "id": o.id,
            "client_id": o.client_id,
            "client_name": o.client.name if o.client else None,
            "order_type": o.order_type,
            "delivery_status": o.delivery_status,
            "delivery_fee": o.delivery_fee,
            "delivery_person_name": o.delivery_person_name,
            "estimated_delivery_time": o.estimated_delivery_time.isoformat() if o.estimated_delivery_time else None,
            "delivered_at": o.delivered_at.isoformat() if o.delivered_at else None,
            "total": o.total,
            "status": o.status,
            "notes": o.notes,
            "address": {
                "street": o.delivery_address.street,
                "number": o.delivery_address.number,
                "neighborhood": o.delivery_address.neighborhood,
                "city": o.delivery_address.city,
                "reference": o.delivery_address.reference,
            } if o.delivery_address else None,
            "created_at": o.created_at.isoformat(),
        })
    return result


@router.put("/orders/{order_id}/status", response_model=dict)
def update_delivery_status(
    order_id: int,
    data: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    new_status = data.get("delivery_status")
    if not new_status:
        raise HTTPException(status_code=400, detail="delivery_status é obrigatório")

    valid_statuses = ["recebido", "em_preparo", "pronto", "saiu_para_entrega", "entregue", "cancelado"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status inválido. Válidos: {', '.join(valid_statuses)}")

    old_status = order.delivery_status
    order.delivery_status = new_status

    if new_status == "entregue":
        from datetime import datetime
from app.utils import utcnow
        order.delivered_at = utcnow()

    # Register event
    event = DeliveryEvent(
        order_id=order.id,
        status=new_status,
        notes=data.get("notes"),
        user_id=current_user.id,
    )
    db.add(event)

    if "delivery_person_name" in data:
        order.delivery_person_name = data["delivery_person_name"]

    db.commit()

    AuditService(db).log(
        action="update", entity_type="order", entity_id=order.id,
        user_id=current_user.id, username=current_user.username,
        details=f"Status de entrega alterado: {old_status} → {new_status}",
    )

    return {"id": order.id, "delivery_status": new_status, "delivered_at": str(order.delivered_at) if order.delivered_at else None}


# ── Delivery Events ────────────────────────────────────────────

@router.get("/events/{order_id}", response_model=list[DeliveryEventOut])
def list_delivery_events(
    order_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    events = db.query(DeliveryEvent).options(
        joinedload(DeliveryEvent.user)
    ).filter(
        DeliveryEvent.order_id == order_id
    ).order_by(DeliveryEvent.created_at).all()

    return [
        DeliveryEventOut(
            id=e.id, order_id=e.order_id, status=e.status,
            notes=e.notes, user_id=e.user_id,
            user_name=e.user.full_name if e.user else None,
            created_at=e.created_at,
        )
        for e in events
    ]
