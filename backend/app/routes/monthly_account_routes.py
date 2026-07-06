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
from app.models.order import Order
from app.models.monthly_account import MonthlyAccount, MonthlyAccountItem
from app.models.signature import Signature
from app.models.payment import Payment
from app.models.payment_method import PaymentMethod
from app.schemas.schemas import (
    MonthlyAccountCreate, MonthlyAccountClose, MonthlyAccountPay,
    MonthlyAccountOut, MonthlyAccountItemOut,
    PaymentOut,
)
from app.auth.auth import get_current_user
from app.services.audit_service import AuditService
from app.services.biometric_service import BiometricService

router = APIRouter(prefix="/api/monthly-accounts", tags=["Monthly Accounts"])


def _calculate_due_date(client: Client, month: int, year: int) -> date | None:
    if not getattr(client, "payment_day", None):
        return None
    day = max(1, min(int(client.payment_day), monthrange(year, month)[1]))
    return date(year, month, day)


@router.get("", response_model=list[MonthlyAccountOut])
def list_monthly_accounts(
    client_id: Optional[int] = None,
    status: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(MonthlyAccount).options(
        joinedload(MonthlyAccount.client),
        joinedload(MonthlyAccount.closer),
        joinedload(MonthlyAccount.payer),
    )
    if client_id:
        query = query.filter(MonthlyAccount.client_id == client_id)
    if status:
        query = query.filter(MonthlyAccount.status == status)
    if month:
        query = query.filter(MonthlyAccount.month == month)
    if year:
        query = query.filter(MonthlyAccount.year == year)

    accounts = query.order_by(MonthlyAccount.year.desc(), MonthlyAccount.month.desc()).offset(skip).limit(limit).all()

    result = []
    for a in accounts:
        items = db.query(MonthlyAccountItem).filter(
            MonthlyAccountItem.monthly_account_id == a.id
        ).all()
        result.append(MonthlyAccountOut(
            id=a.id,
            client_id=a.client_id,
            client_name=a.client.name if a.client else None,
            month=a.month,
            year=a.year,
            total=a.total,
            status=a.status,
            client_is_account_client=getattr(a.client, "is_account_client", False),
            due_date=a.due_date,
            closed_at=a.closed_at,
            closed_by=a.closed_by,
            closed_by_name=a.closer.full_name if a.closer else None,
            biometric_verification_id=a.biometric_verification_id,
            biometric_verified_at=a.biometric_verified_at,
            paid_at=a.paid_at,
            paid_by=a.paid_by,
            paid_by_name=a.payer.full_name if a.payer else None,
            notes=a.notes,
            items=[MonthlyAccountItemOut.model_validate(i) for i in items],
            created_at=a.created_at,
            updated_at=a.updated_at,
        ))
    return result


@router.get("/{account_id}", response_model=MonthlyAccountOut)
def get_monthly_account(account_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    a = db.query(MonthlyAccount).options(
        joinedload(MonthlyAccount.client),
        joinedload(MonthlyAccount.closer),
        joinedload(MonthlyAccount.payer),
    ).filter(MonthlyAccount.id == account_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Monthly account not found")

    items = db.query(MonthlyAccountItem).filter(
        MonthlyAccountItem.monthly_account_id == a.id
    ).all()

    return MonthlyAccountOut(
        id=a.id,
        client_id=a.client_id,
        client_name=a.client.name if a.client else None,
        month=a.month,
        year=a.year,
        total=a.total,
        status=a.status,
        client_is_account_client=getattr(a.client, "is_account_client", False),
        due_date=a.due_date,
        closed_at=a.closed_at,
        closed_by=a.closed_by,
        closed_by_name=a.closer.full_name if a.closer else None,
        biometric_verification_id=a.biometric_verification_id,
        biometric_verified_at=a.biometric_verified_at,
        paid_at=a.paid_at,
        paid_by=a.paid_by,
        paid_by_name=a.payer.full_name if a.payer else None,
        notes=a.notes,
        items=[MonthlyAccountItemOut.model_validate(i) for i in items],
        created_at=a.created_at,
        updated_at=a.updated_at,
    )


@router.post("", response_model=MonthlyAccountOut, status_code=201)
def create_monthly_account(
    data: MonthlyAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(MonthlyAccount).filter(
        MonthlyAccount.client_id == data.client_id,
        MonthlyAccount.month == data.month,
        MonthlyAccount.year == data.year,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Monthly account already exists for this client/period")

    client = db.query(Client).filter(Client.id == data.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    account = MonthlyAccount(
        client_id=data.client_id,
        month=data.month,
        year=data.year,
        total=0.0,
        due_date=_calculate_due_date(client, data.month, data.year),
        status="open",
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    return get_monthly_account(account.id, db, current_user)


@router.post("/{account_id}/close", response_model=MonthlyAccountOut)
def close_monthly_account(
    account_id: int,
    data: MonthlyAccountClose,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.name not in ("admin", "financial"):
        raise HTTPException(status_code=403, detail="Only financial and admin can close accounts")

    account = db.query(MonthlyAccount).filter(MonthlyAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Monthly account not found")
    if account.status != "open":
        raise HTTPException(status_code=400, detail=f"Account is already {account.status}")

    # Find all confirmed orders for this client in the period
    orders = db.query(Order).filter(
        Order.client_id == account.client_id,
        extract("month", Order.created_at) == account.month,
        extract("year", Order.created_at) == account.year,
        Order.status.in_(["confirmed", "open"]),
    ).all()

    total = 0.0
    for order in orders:
        # Update order status
        order.status = "invoiced"
        item = MonthlyAccountItem(
            monthly_account_id=account.id,
            order_id=order.id,
            order_total=order.total,
        )
        db.add(item)
        total += order.total

    account.total = total
    account.status = "closed"
    account.closed_at = utcnow()
    account.closed_by = current_user.id
    if data.notes:
        account.notes = data.notes

    db.commit()

    AuditService(db).log(
        action="close",
        entity_type="monthly_account",
        entity_id=account.id,
        user_id=current_user.id,
        username=current_user.username,
        ip_address=request.client.host if request.client else None,
        details=f"Closed monthly account for client #{account.client_id}, month {account.month}/{account.year}, total R$ {total:.2f}",
    )

    return get_monthly_account(account.id, db, current_user)


@router.post("/{account_id}/biometric-verify")
def verify_biometric_for_account(
    account_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Verify client fingerprint to confirm a monthly account (replaces old signature flow)."""
    if current_user.role.name not in ("admin", "financial"):
        raise HTTPException(status_code=403, detail="Only financial and admin can verify biometrics")

    account = db.query(MonthlyAccount).filter(MonthlyAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Monthly account not found")
    if account.status not in ("closed", "confirmed_by_biometrics"):
        raise HTTPException(status_code=400, detail=f"Account must be closed to verify biometrics, current status: {account.status}")

    # Perform biometric verification
    service = BiometricService(db)
    success, status, message = service.verify_client(
        client_id=account.client_id,
        monthly_account_id=account.id,
        performed_by=current_user.id,
        ip_address=request.client.host if request.client else None,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message": message,
        "account_id": account.id,
        "status": status,
    }


@router.post("/{account_id}/pay", response_model=MonthlyAccountOut)
def pay_monthly_account(
    account_id: int,
    data: MonthlyAccountPay,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.name not in ("admin", "financial"):
        raise HTTPException(status_code=403, detail="Only financial and admin can register payments")

    account = db.query(MonthlyAccount).filter(MonthlyAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Monthly account not found")
    if account.status not in ("confirmed_by_biometrics", "closed"):
        raise HTTPException(status_code=400, detail=f"Account must be closed/confirmed to pay, current status: {account.status}")
    method = db.query(PaymentMethod).filter(
        PaymentMethod.code == data.payment_method,
        PaymentMethod.is_active == True,
    ).first()
    if not method:
        raise HTTPException(status_code=400, detail="Forma de pagamento inválida ou inativa")

    payment = Payment(
        monthly_account_id=account.id,
        client_id=account.client_id,
        user_id=current_user.id,
        amount=account.total,
        payment_method=data.payment_method,
        notes=data.notes,
    )
    db.add(payment)
    db.flush()

    account.status = "paid"
    account.paid_at = utcnow()
    account.paid_by = current_user.id

    signature_data = data.signature_data
    if signature_data:
        bio = (
            db.query(Signature)
            .filter(
                Signature.monthly_account_id == account.id,
                Signature.client_id == account.client_id,
            )
            .first()
        )
        verification_hash = getattr(getattr(bio, "verification_hash", None), "verification_hash", None)
        if verification_hash is None and signature_data:
            verification_hash = f"{signature_data}:{account.id}"
        signature = Signature(
            monthly_account_id=account.id,
            client_id=account.client_id,
            user_id=current_user.id,
            signature_data=signature_data,
            signed_value=account.total,
            verification_hash=verification_hash,
            ip_address=request.client.host if request.client else None,
            device_info="web_payment",
        )
        db.add(signature)

    db.commit()

    AuditService(db).log(
        action="pay",
        entity_type="payment",
        entity_id=payment.id,
        user_id=current_user.id,
        username=current_user.username,
        ip_address=request.client.host if request.client else None,
        details=f"Payment registered for account #{account.id}, amount R$ {account.total:.2f}",
    )

    return get_monthly_account(account.id, db, current_user)
