from calendar import monthrange
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import extract
from sqlalchemy.orm import Session, joinedload

from app.auth.auth import get_current_user
from app.database import get_db
from app.models.client import Client
from app.models.company import Company
from app.models.company_monthly_account import (
    CompanyMonthlyAccount,
    CompanyMonthlyAccountItem,
    CompanyPayment,
)
from app.models.monthly_account import MonthlyAccount, MonthlyAccountItem
from app.models.order import Order
from app.models.payment_method import PaymentMethod
from app.models.user import User
from app.schemas.schemas import (
    CompanyMonthlyAccountCreate,
    CompanyMonthlyAccountItemOut,
    CompanyMonthlyAccountOut,
    CompanyMonthlyAccountPay,
)
from app.services.audit_service import AuditService
from app.utils import utcnow

router = APIRouter(prefix="/api/company-monthly-accounts", tags=["Company Monthly Accounts"])


def _due_date(company: Company, month: int, year: int) -> date | None:
    if company.payment_day is None:
        return None
    day = max(1, min(int(company.payment_day), monthrange(year, month)[1]))
    return date(year, month, day)


def _serialize(account: CompanyMonthlyAccount) -> CompanyMonthlyAccountOut:
    return CompanyMonthlyAccountOut(
        id=account.id,
        company_id=account.company_id,
        company_name=(account.company.trade_name or account.company.legal_name) if account.company else None,
        month=account.month,
        year=account.year,
        total=account.total or 0.0,
        due_date=account.due_date,
        status=account.status,
        closed_at=account.closed_at,
        closed_by_name=account.closer.full_name if account.closer else None,
        paid_at=account.paid_at,
        paid_by_name=account.payer.full_name if account.payer else None,
        payment_method=account.payment_method,
        over_limit=bool(account.over_limit),
        notes=account.notes,
        items=[
            CompanyMonthlyAccountItemOut(
                id=item.id,
                monthly_account_id=item.monthly_account_id,
                client_id=item.client_id,
                client_name=item.client.name if item.client else None,
                client_total=item.client_total,
                created_at=item.created_at,
            )
            for item in account.items
        ],
        created_at=account.created_at,
        updated_at=account.updated_at,
    )


def _load(account_id: int, db: Session) -> CompanyMonthlyAccount | None:
    return (
        db.query(CompanyMonthlyAccount)
        .options(
            joinedload(CompanyMonthlyAccount.company),
            joinedload(CompanyMonthlyAccount.closer),
            joinedload(CompanyMonthlyAccount.payer),
            joinedload(CompanyMonthlyAccount.items).joinedload(CompanyMonthlyAccountItem.client),
        )
        .filter(CompanyMonthlyAccount.id == account_id)
        .first()
    )


@router.get("", response_model=list[CompanyMonthlyAccountOut])
def list_company_accounts(
    company_id: Optional[int] = None,
    status: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(CompanyMonthlyAccount)
    if company_id:
        query = query.filter(CompanyMonthlyAccount.company_id == company_id)
    if status:
        query = query.filter(CompanyMonthlyAccount.status == status)
    if month:
        query = query.filter(CompanyMonthlyAccount.month == month)
    if year:
        query = query.filter(CompanyMonthlyAccount.year == year)
    accounts = query.order_by(CompanyMonthlyAccount.year.desc(), CompanyMonthlyAccount.month.desc()).offset(skip).limit(limit).all()
    return [_serialize(_load(account.id, db)) for account in accounts]


@router.get("/{account_id}", response_model=CompanyMonthlyAccountOut)
def get_company_account(account_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    account = _load(account_id, db)
    if account is None:
        raise HTTPException(status_code=404, detail="Company monthly account not found")
    return _serialize(account)


@router.post("", response_model=CompanyMonthlyAccountOut, status_code=201)
def create_company_account(
    data: CompanyMonthlyAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = db.query(Company).filter(Company.id == data.company_id).first()
    if company is None or company.status != "active":
        raise HTTPException(status_code=404, detail="Active company not found")
    existing = db.query(CompanyMonthlyAccount).filter(
        CompanyMonthlyAccount.company_id == data.company_id,
        CompanyMonthlyAccount.month == data.month,
        CompanyMonthlyAccount.year == data.year,
    ).first()
    if existing is not None:
        raise HTTPException(status_code=400, detail="Company monthly account already exists for this period")
    account = CompanyMonthlyAccount(
        company_id=company.id,
        month=data.month,
        year=data.year,
        due_date=_due_date(company, data.month, data.year),
        status="open",
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return _serialize(_load(account.id, db))


@router.post("/{account_id}/close", response_model=CompanyMonthlyAccountOut)
def close_company_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.name not in ("admin", "financial"):
        raise HTTPException(status_code=403, detail="Only financial and admin can close company accounts")
    account = _load(account_id, db)
    if account is None:
        raise HTTPException(status_code=404, detail="Company monthly account not found")
    if account.status != "open":
        raise HTTPException(status_code=400, detail=f"Account is already {account.status}")

    members = db.query(Client).filter(Client.company_id == account.company_id, Client.status == "active").all()
    for client in members:
        individual = db.query(MonthlyAccount).filter(
            MonthlyAccount.client_id == client.id,
            MonthlyAccount.month == account.month,
            MonthlyAccount.year == account.year,
        ).first()
        if individual is None:
            individual = MonthlyAccount(
                client_id=client.id,
                month=account.month,
                year=account.year,
                total=0.0,
                due_date=_due_date(account.company, account.month, account.year),
                status="open",
            )
            db.add(individual)
            db.flush()

        orders = db.query(Order).filter(
            Order.client_id == client.id,
            extract("month", Order.created_at) == account.month,
            extract("year", Order.created_at) == account.year,
            Order.status.in_(["confirmed", "open"]),
        ).all()
        for order in orders:
            order.status = "invoiced"
            db.add(MonthlyAccountItem(monthly_account_id=individual.id, order_id=order.id, order_total=order.total))
            individual.total = (individual.total or 0.0) + order.total
        if individual.status == "open":
            individual.status = "closed"
            individual.closed_at = utcnow()
            individual.closed_by = current_user.id
        individual.over_limit = bool(
            client.monthly_limit and client.monthly_limit > 0 and individual.total > client.monthly_limit
        )
        existing_item = db.query(CompanyMonthlyAccountItem).filter(
            CompanyMonthlyAccountItem.company_monthly_account_id == account.id,
            CompanyMonthlyAccountItem.client_id == client.id,
        ).first()
        if existing_item is None:
            db.add(CompanyMonthlyAccountItem(
                company_monthly_account_id=account.id,
                monthly_account_id=individual.id,
                client_id=client.id,
                client_total=individual.total or 0.0,
            ))
        else:
            existing_item.client_total = individual.total or 0.0

    db.flush()
    total = sum(
        item.client_total
        for item in db.query(CompanyMonthlyAccountItem)
        .filter(CompanyMonthlyAccountItem.company_monthly_account_id == account.id)
        .all()
    )
    account.total = total
    account.over_limit = bool(
        account.company.monthly_limit and account.company.monthly_limit > 0 and total > account.company.monthly_limit
    )
    account.status = "closed"
    account.closed_at = utcnow()
    account.closed_by = current_user.id
    db.commit()
    AuditService(db).log(
        action="close",
        entity_type="company_monthly_account",
        entity_id=account.id,
        user_id=current_user.id,
        username=current_user.username,
        details=f"Closed company account for {account.company.legal_name}, total R$ {total:.2f}",
    )
    return _serialize(_load(account.id, db))


@router.post("/{account_id}/pay", response_model=CompanyMonthlyAccountOut)
def pay_company_account(
    account_id: int,
    data: CompanyMonthlyAccountPay,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.name not in ("admin", "financial"):
        raise HTTPException(status_code=403, detail="Only financial and admin can register company payments")
    account = _load(account_id, db)
    if account is None:
        raise HTTPException(status_code=404, detail="Company monthly account not found")
    if account.status not in ("closed", "confirmed_by_biometrics"):
        raise HTTPException(status_code=400, detail=f"Account must be closed to pay, current status: {account.status}")
    method = db.query(PaymentMethod).filter(PaymentMethod.code == data.payment_method, PaymentMethod.is_active == True).first()
    if method is None:
        raise HTTPException(status_code=400, detail="Invalid or inactive payment method")
    db.add(CompanyPayment(
        company_monthly_account_id=account.id,
        company_id=account.company_id,
        user_id=current_user.id,
        amount=account.total,
        payment_method=data.payment_method,
        notes=data.notes,
    ))
    account.status = "paid"
    account.paid_at = utcnow()
    account.paid_by = current_user.id
    account.payment_method = data.payment_method
    db.commit()
    AuditService(db).log(
        action="pay",
        entity_type="company_monthly_account",
        entity_id=account.id,
        user_id=current_user.id,
        username=current_user.username,
        details=f"Paid company account #{account.id}, amount R$ {account.total:.2f}",
    )
    return _serialize(_load(account.id, db))
