from calendar import monthrange
from datetime import date, datetime
from app.utils import utcnow
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import extract
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.client import Client
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.monthly_account import MonthlyAccount
from app.models.signature import Signature
from app.schemas.schemas import (
    OrderCreate,
    OrderUpdate,
    OrderOut,
    OrderItemOut,
    SignatureCreate,
    SignatureOut,
)
from app.auth.auth import get_current_user
from app.routes.biometric_routes import consume_verified_token
from app.services.audit_service import AuditService
from app.services.biometric_service import BiometricService
from app.services.stock_service import StockService

router = APIRouter(prefix="/api/orders", tags=["Orders"])


@router.get("", response_model=list[OrderOut])
def list_orders(
    client_id: Optional[int] = None,
    status: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Order).options(
        joinedload(Order.client), joinedload(Order.user), joinedload(Order.items)
    )
    if client_id:
        query = query.filter(Order.client_id == client_id)
    if status:
        query = query.filter(Order.status == status)
    if month:
        query = query.filter(extract("month", Order.created_at) == month)
    if year:
        query = query.filter(extract("year", Order.created_at) == year)

    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for o in orders:
        result.append(OrderOut(
            id=o.id,
            client_id=o.client_id,
            client_name=o.client.name if o.client else None,
            user_id=o.user_id,
            user_name=o.user.full_name if o.user else None,
            status=o.status,
            notes=o.notes,
            total=o.total,
            items=[OrderItemOut.model_validate(i) for i in o.items],
            created_at=o.created_at,
            updated_at=o.updated_at,
        ))
    return result


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    order = db.query(Order).options(
        joinedload(Order.client), joinedload(Order.user), joinedload(Order.items)
    ).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return OrderOut(
        id=order.id,
        client_id=order.client_id,
        client_name=order.client.name if order.client else None,
        user_id=order.user_id,
        user_name=order.user.full_name if order.user else None,
        status=order.status,
        notes=order.notes,
        total=order.total,
        items=[OrderItemOut.model_validate(i) for i in order.items],
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


def _calculate_due_date(client: Client, month: int, year: int) -> date | None:
    if not client.payment_day:
        return None
    day = max(1, min(int(client.payment_day), monthrange(year, month)[1]))
    return date(year, month, day)


def _find_or_create_monthly_account(client: Client, month: int, year: int, db: Session) -> MonthlyAccount:
    account = db.query(MonthlyAccount).filter(
        MonthlyAccount.client_id == client.id,
        MonthlyAccount.month == month,
        MonthlyAccount.year == year,
    ).first()
    if account:
        if not getattr(account, "due_date", None):
            account.due_date = _calculate_due_date(client, month, year)
        return account
    account = MonthlyAccount(
        client_id=client.id,
        month=month,
        year=year,
        total=0.0,
        due_date=_calculate_due_date(client, month, year),
        status="open",
    )
    db.add(account)
    db.flush()
    return account


@router.post("", response_model=OrderOut, status_code=201)
def create_order(
    data: OrderCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client = db.query(Client).filter(Client.id == data.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    if client.status == "inactive":
        raise HTTPException(status_code=400, detail="Client is inactive")

    if not data.items:
        raise HTTPException(status_code=400, detail="Order must have at least one item")
    if data.payment_mode != "monthly_account":
        raise HTTPException(status_code=400, detail="Invalid payment mode")

    now = utcnow()
    total = sum(item.total for item in data.items)
    payment_mode = data.payment_mode

    order = Order(
        client_id=data.client_id,
        user_id=current_user.id,
        status="confirmed",
        order_type="conta_mensal",
        notes=data.notes,
        total=total,
    )
    db.add(order)
    db.flush()

    for item_data in data.items:
        product = db.query(Product).filter(Product.id == item_data.product_id).first()
        order_item = OrderItem(
            order_id=order.id,
            product_id=item_data.product_id,
            product_name=item_data.product_name,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            total=item_data.total,
        )
        db.add(order_item)

    account = _find_or_create_monthly_account(
        client=client,
        month=now.month,
        year=now.year,
        db=db,
    )
    if data.tab_id:
        account = db.query(MonthlyAccount).filter(MonthlyAccount.id == data.tab_id).first() or account

    account.total = (account.total or 0.0) + total
    order.tab_id = account.id

    if data.confirm_with_biometric:
        if data.biometric_verification_token:
            if not consume_verified_token(data.biometric_verification_token, client.id):
                raise HTTPException(status_code=400, detail="Token de digital inválido ou expirado")
        else:
            success, _, message = BiometricService(db).verify_identity(
                client_id=client.id,
                performed_by=current_user.id,
                ip_address=request.client.host if request.client else None,
                detail_context=f"Lançamento do pedido #{order.id} na conta mensal #{account.id}",
            )
            if not success:
                raise HTTPException(status_code=400, detail=message)

    db.commit()
    db.refresh(order)
    db.refresh(account)

    stock_alerts = StockService(db).deduct_stock_for_order(order.id)

    AuditService(db).log(
        action="create",
        entity_type="order",
        entity_id=order.id,
        user_id=current_user.id,
        username=current_user.username,
        ip_address=request.client.host if request.client else None,
        details=(
            f"Created order for client {client.name}, total R$ {total:.2f}, "
            f"mode {payment_mode}, linked to account #{account.id}. "
            f"Stock alerts: {'; '.join(stock_alerts) if stock_alerts else 'none'}"
        ),
    )

    order = db.query(Order).options(
        joinedload(Order.client), joinedload(Order.user), joinedload(Order.items)
    ).filter(Order.id == order.id).first()

    return OrderOut(
        id=order.id,
        client_id=order.client_id,
        client_name=order.client.name if order.client else None,
        user_id=order.user_id,
        user_name=order.user.full_name if order.user else None,
        status=order.status,
        notes=order.notes,
        total=order.total,
        items=[OrderItemOut.model_validate(i) for i in order.items],
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.put("/{order_id}", response_model=OrderOut)
def update_order(
    order_id: int,
    data: OrderUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).options(
        joinedload(Order.client), joinedload(Order.user), joinedload(Order.items)
    ).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    before = {"status": order.status}
    if data.status is not None:
        if data.status == "cancelled":
            AuditService(db).log(
                action="cancel",
                entity_type="order",
                entity_id=order.id,
                user_id=current_user.id,
                username=current_user.username,
                before_state=before,
                after_state={"status": "cancelled"},
                ip_address=request.client.host if request.client else None,
                details=f"Cancelled order #{order.id}",
            )
        order.status = data.status
    if data.notes is not None:
        order.notes = data.notes

    db.commit()
    db.refresh(order)

    order = db.query(Order).options(
        joinedload(Order.client), joinedload(Order.user), joinedload(Order.items)
    ).filter(Order.id == order.id).first()

    return OrderOut(
        id=order.id,
        client_id=order.client_id,
        client_name=order.client.name if order.client else None,
        user_id=order.user_id,
        user_name=order.user.full_name if order.user else None,
        status=order.status,
        notes=order.notes,
        total=order.total,
        items=[OrderItemOut.model_validate(i) for i in order.items],
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.post("/{order_id}/signature", response_model=SignatureOut, status_code=201)
def add_order_signature(
    order_id: int,
    data: SignatureCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    client = db.query(Client).filter(Client.id == order.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # ensure account exists
    now = utcnow()
    account = _find_or_create_monthly_account(
        client=client,
        month=now.month,
        year=now.year,
        db=db,
    )
    db.flush()

    signature = Signature(
        monthly_account_id=account.id,
        client_id=order.client_id,
        user_id=current_user.id,
        signature_data=data.signature_data,
        signed_value=data.signed_value or order.total,
        ip_address=data.ip_address or (request.client.host if request.client else None),
        device_info=data.device_info or "web",
    )
    db.add(signature)
    account.total = (account.total or 0.0) + (data.signed_value or order.total)
    db.commit()
    db.refresh(signature)
    return signature
