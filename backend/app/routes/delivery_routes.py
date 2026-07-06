from typing import Optional
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.database import get_db
from app.models.user import User
from app.models.delivery import DeliveryPlatform
from app.models.delivery import DeliveryOrder
from app.models.delivery import DeliveryPlatformItem
from app.schemas.schemas import (
    DeliveryPlatformCreate,
    DeliveryPlatformOut,
    DeliveryOrderCreate,
    DeliveryOrderIncoming,
    DeliveryOrderOut,
    DeliveryPlatformItemCreate,
    DeliveryPlatformItemOut,
)
from app.auth.auth import get_current_user
from app.services.audit_service import AuditService


router = APIRouter(prefix="/api/delivery", tags=["Delivery"])

PLATFORMS = ["iFood", "Rappi", "Uber Eats", "99Food", "Glovo"]


def _normalize_slug(name: str) -> str:
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def _ensure_platform(db: Session, name: str) -> DeliveryPlatform:
    if name not in PLATFORMS:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {name}")
    slug = _normalize_slug(name)
    platform = db.query(DeliveryPlatform).filter(DeliveryPlatform.slug == slug).first()
    if not platform:
        platform = DeliveryPlatform(name=name, slug=slug, active=True)
        db.add(platform)
        db.commit()
        db.refresh(platform)
    return platform


@router.get("/platforms", response_model=list[DeliveryPlatformOut])
def list_platforms(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(DeliveryPlatform).order_by(DeliveryPlatform.created_at.asc()).all()


@router.post("/platforms", response_model=DeliveryPlatformOut)
def create_platform(data: DeliveryPlatformCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = db.query(DeliveryPlatform).filter(DeliveryPlatform.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Platform already exists")
    platform = DeliveryPlatform(
        name=data.name,
        slug=_normalize_slug(data.name),
        active=data.active,
        api_base_url=data.api_base_url,
        webhook_secret=data.webhook_secret,
        settings=json_dumps(data.settings) if data.settings is not None else None,
    )
    db.add(platform)
    db.commit()
    db.refresh(platform)
    AuditService(db).log(
        action="create",
        entity_type="delivery_platform",
        entity_id=platform.id,
        user_id=current_user.id,
        username=current_user.username,
        details=f"Created delivery platform {platform.name}",
    )
    db.commit()
    return platform


def _serialize_platform(platform: DeliveryPlatform) -> DeliveryPlatformOut:
    return DeliveryPlatformOut(
        id=platform.id,
        name=platform.name,
        slug=platform.slug,
        active=platform.active,
        api_base_url=platform.api_base_url,
        webhook_secret=platform.webhook_secret,
        settings=json.loads(platform.settings) if isinstance(platform.settings, str) else platform.settings,
        created_at=platform.created_at,
        updated_at=platform.updated_at,
    )


def _serialize_item(item: DeliveryPlatformItem) -> DeliveryPlatformItemOut:
    return DeliveryPlatformItemOut(
        id=item.id,
        delivery_order_id=item.delivery_order_id,
        external_item_id=item.external_item_id,
        product_id=item.product_id,
        product_name=item.product_name,
        quantity=item.quantity,
        unit_price=item.unit_price,
        total=item.total,
        notes=item.notes,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _serialize_order(order: DeliveryOrder) -> DeliveryOrderOut:
    return DeliveryOrderOut(
        id=order.id,
        platform_id=order.platform_id,
        external_order_id=order.external_order_id,
        client_name=order.client_name,
        client_phone=order.client_phone,
        address=order.address,
        payment_method=order.payment_method,
        subtotal=order.subtotal,
        delivery_fee=order.delivery_fee,
        discount=order.discount,
        total=order.total,
        status=order.status,
        raw_payload=order.raw_payload,
        received_at=order.received_at,
        acknowledged_at=order.acknowledged_at,
        cancelled_at=order.cancelled_at,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=[_serialize_item(i) for i in order.items],
    )


@router.get("/orders", response_model=list[DeliveryOrderOut])
def list_delivery_orders(
    platform_slug: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(DeliveryOrder).options(joinedload(DeliveryOrder.items)).join(DeliveryPlatform, DeliveryOrder.platform_id == DeliveryPlatform.id)
    if platform_slug:
        query = query.filter(DeliveryPlatform.slug == platform_slug)
    if status:
        query = query.filter(DeliveryOrder.status == status)
    orders = query.order_by(DeliveryOrder.received_at.desc()).limit(limit).all()
    return [_serialize_order(o) for o in orders]


@router.get("/orders/{order_id}", response_model=DeliveryOrderOut)
def get_delivery_order(order_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    order = db.query(DeliveryOrder).options(joinedload(DeliveryOrder.items)).filter(DeliveryOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Delivery order not found")
    return _serialize_order(order)


@router.post("/orders/incoming", response_model=DeliveryOrderOut, status_code=201)
def create_delivery_order_manually(data: DeliveryOrderCreate, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    platform = None
    platform_name = data.platform_slug
    if not platform_name:
        platform_name = PLATFORMS[0]
    if platform_name:
        platform = db.query(DeliveryPlatform).filter(DeliveryPlatform.slug == _normalize_slug(platform_name)).first()
        if not platform:
            platform = _ensure_platform(db, platform_name)

    order = DeliveryOrder(
        platform_id=platform.id,
        external_order_id=data.external_order_id,
        client_name=data.client_name,
        client_phone=data.client_phone,
        address=data.address,
        payment_method=data.payment_method,
        subtotal=data.subtotal,
        delivery_fee=data.delivery_fee,
        discount=data.discount,
        total=data.total,
        status="pending",
        raw_payload=json_dumps({"manual": True, "notes": data.notes}) if data.notes else None,
    )
    db.add(order)
    db.flush()

    for item in data.items:
        db.add(DeliveryPlatformItem(
            delivery_order_id=order.id,
            external_item_id=item.external_item_id,
            product_id=item.product_id,
            product_name=item.product_name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total=item.total,
            notes=item.notes,
        ))

    db.add(order)
    db.commit()
    db.refresh(order)
    order = db.query(DeliveryOrder).options(joinedload(DeliveryOrder.items)).filter(DeliveryOrder.id == order.id).first()
    AuditService(db).log(
        action="create",
        entity_type="delivery_order",
        entity_id=order.id,
        user_id=current_user.id,
        username=current_user.username,
        ip_address=request.client.host if request.client else None,
        details=f"Created delivery order for platform {platform.name}",
    )
    db.commit()
    return _serialize_order(order)


@router.post("/webhook/{platform_slug}", response_model=DeliveryOrderOut)
def delivery_webhook(platform_slug: str, payload: DeliveryOrderIncoming, request: Request, db: Session = Depends(get_db)):
    secret = request.headers.get("x-webhook-secret") or request.headers.get("x-hub-signature") or request.headers.get("authorization")
    platform = db.query(DeliveryPlatform).filter(DeliveryPlatform.slug == platform_slug, DeliveryPlatform.active == True).first()
    if not platform:
        platform = _ensure_platform(db, platform_slug)

    if platform.webhook_secret and secret != platform.webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    existing = None
    if payload.external_order_id:
        existing = (
            db.query(DeliveryOrder)
            .filter(DeliveryOrder.platform_id == platform.id, DeliveryOrder.external_order_id == payload.external_order_id)
            .first()
        )
    if existing:
        status = existing.status
        if status == "pending":
            existing.acknowledged_at = utcnow()
            existing.status = "acknowledged"
        db.commit()
        db.refresh(existing)
        order = db.query(DeliveryOrder).options(joinedload(DeliveryOrder.items)).filter(DeliveryOrder.id == existing.id).first()
        return _serialize_order(order)

    order = DeliveryOrder(
        platform_id=platform.id,
        external_order_id=payload.external_order_id,
        client_name=payload.client_name,
        client_phone=payload.client_phone,
        address=payload.address,
        payment_method=payload.payment_method,
        subtotal=payload.subtotal,
        delivery_fee=payload.delivery_fee,
        discount=payload.discount,
        total=payload.total,
        status="acknowledged",
        raw_payload=payload.raw_payload or json_dumps(payload.dict()),
    )
    db.add(order)
    db.flush()

    for item in payload.items:
        db.add(DeliveryPlatformItem(
            delivery_order_id=order.id,
            external_item_id=item.external_item_id,
            product_id=item.product_id,
            product_name=item.product_name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total=item.total,
            notes=item.notes,
        ))

    db.commit()
    db.refresh(order)
    order = db.query(DeliveryOrder).options(joinedload(DeliveryOrder.items)).filter(DeliveryOrder.id == order.id).first()
    AuditService(db).log(
        action="webhook",
        entity_type="delivery_order",
        entity_id=order.id,
        user_id=None,
        username="webhook",
        ip_address=request.client.host if request.client else None,
        details=f"Webhook received for {platform.name}: external_order_id={payload.external_order_id}",
    )
    db.commit()
    return _serialize_order(order)


@router.post("/orders/{order_id}/ack", response_model=DeliveryOrderOut)
def acknowledge_order(order_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(DeliveryOrder).filter(DeliveryOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Delivery order not found")
    order.status = "acknowledged"
    order.acknowledged_at = utcnow()
    db.commit()
    db.refresh(order)
    order = db.query(DeliveryOrder).options(joinedload(DeliveryOrder.items)).filter(DeliveryOrder.id == order.id).first()
    AuditService(db).log(
        action="ack",
        entity_type="delivery_order",
        entity_id=order.id,
        user_id=current_user.id,
        username=current_user.username,
        ip_address=request.client.host if request.client else None,
        details=f"Acknowledged delivery order {order.id}",
    )
    db.commit()
    return _serialize_order(order)


@router.post("/orders/{order_id}/cancel", response_model=DeliveryOrderOut)
def cancel_order(order_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(DeliveryOrder).filter(DeliveryOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Delivery order not found")
    order.status = "cancelled"
    order.cancelled_at = utcnow()
    db.commit()
    db.refresh(order)
    order = db.query(DeliveryOrder).options(joinedload(DeliveryOrder.items)).filter(DeliveryOrder.id == order.id).first()
    AuditService(db).log(
        action="cancel",
        entity_type="delivery_order",
        entity_id=order.id,
        user_id=current_user.id,
        username=current_user.username,
        ip_address=request.client.host if request.client else None,
        details=f"Cancelled delivery order {order.id}",
    )
    db.commit()
    return _serialize_order(order)


@router.post("/orders/{order_id}/convert-order", response_model=DeliveryOrderOut)
def convert_to_internal_order(order_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(DeliveryOrder).options(joinedload(DeliveryOrder.items)).filter(DeliveryOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Delivery order not found")
    order.status = "converted"
    db.commit()
    db.refresh(order)
    AuditService(db).log(
        action="convert",
        entity_type="delivery_order",
        entity_id=order.id,
        user_id=current_user.id,
        username=current_user.username,
        ip_address=request.client.host if request.client else None,
        details=f"Converted delivery order {order.id} to internal order",
    )
    db.commit()
    return _serialize_order(order)


@router.get("/platforms/{slug}", response_model=DeliveryPlatformOut)
def get_platform_by_slug(slug: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    platform = db.query(DeliveryPlatform).filter(DeliveryPlatform.slug == slug).first()
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")
    return _serialize_platform(platform)
