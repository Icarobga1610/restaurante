from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload

from app.auth.auth import get_current_user
from app.database import get_db
from app.models.client import Client
from app.models.company import Company
from app.models.user import User
from app.schemas.schemas import CompanyCreate, CompanyOut, CompanyUpdate, ClientOut
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/companies", tags=["Companies"])


def _validate_payment_day(payment_day: int | None) -> None:
    if payment_day is not None and not 1 <= payment_day <= 31:
        raise HTTPException(status_code=400, detail="Payment day must be between 1 and 31")


def _serialize(company: Company) -> CompanyOut:
    return CompanyOut(
        id=company.id,
        legal_name=company.legal_name,
        trade_name=company.trade_name,
        document=company.document,
        phone=company.phone,
        email=company.email,
        address=company.address,
        monthly_limit=company.monthly_limit,
        payment_day=company.payment_day,
        status=company.status,
        notes=company.notes,
        member_count=len(company.members or []),
        created_at=company.created_at,
        updated_at=company.updated_at,
    )


@router.get("", response_model=list[CompanyOut])
def list_companies(
    status: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Company).options(joinedload(Company.members))
    if status:
        query = query.filter(Company.status == status)
    if search:
        query = query.filter(
            Company.legal_name.ilike(f"%{search}%")
            | Company.trade_name.ilike(f"%{search}%")
            | Company.document.ilike(f"%{search}%")
        )
    return [_serialize(company) for company in query.order_by(Company.legal_name).offset(skip).limit(limit).all()]


@router.get("/{company_id}", response_model=CompanyOut)
def get_company(company_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    company = db.query(Company).options(joinedload(Company.members)).filter(Company.id == company_id).first()
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return _serialize(company)


@router.get("/{company_id}/members", response_model=list[ClientOut])
def list_members(company_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return (
        db.query(Client)
        .options(joinedload(Client.company))
        .filter(Client.company_id == company_id)
        .order_by(Client.name)
        .all()
    )


@router.post("", response_model=CompanyOut, status_code=201)
def create_company(
    data: CompanyCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.name != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create companies")
    _validate_payment_day(data.payment_day)
    if db.query(Company).filter(Company.document == data.document).first() is not None:
        raise HTTPException(status_code=400, detail="Company document already exists")

    company = Company(**data.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    AuditService(db).log(
        action="create",
        entity_type="company",
        entity_id=company.id,
        user_id=current_user.id,
        username=current_user.username,
        ip_address=request.client.host if request.client else None,
        details=f"Created company {company.legal_name}",
    )
    return _serialize(company)


@router.put("/{company_id}", response_model=CompanyOut)
def update_company(
    company_id: int,
    data: CompanyUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.name != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update companies")
    company = db.query(Company).options(joinedload(Company.members)).filter(Company.id == company_id).first()
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    _validate_payment_day(data.payment_day)
    if data.document and data.document != company.document:
        duplicate = db.query(Company).filter(Company.document == data.document, Company.id != company_id).first()
        if duplicate is not None:
            raise HTTPException(status_code=400, detail="Company document already exists")
    before = {"legal_name": company.legal_name, "status": company.status, "monthly_limit": company.monthly_limit}
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(company, key, value)
    db.commit()
    db.refresh(company)
    AuditService(db).log(
        action="update",
        entity_type="company",
        entity_id=company.id,
        user_id=current_user.id,
        username=current_user.username,
        before_state=before,
        after_state={"legal_name": company.legal_name, "status": company.status, "monthly_limit": company.monthly_limit},
        ip_address=request.client.host if request.client else None,
        details=f"Updated company {company.legal_name}",
    )
    return _serialize(company)


@router.post("/{company_id}/members/{client_id}", response_model=ClientOut)
def link_member(
    company_id: int,
    client_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.name != "admin":
        raise HTTPException(status_code=403, detail="Only admins can link company members")
    company = db.query(Company).filter(Company.id == company_id).first()
    client = db.query(Client).filter(Client.id == client_id).first()
    if company is None or company.status != "active":
        raise HTTPException(status_code=404, detail="Active company not found")
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    client.company_id = company.id
    db.commit()
    db.refresh(client)
    AuditService(db).log(
        action="link",
        entity_type="company_member",
        entity_id=client.id,
        user_id=current_user.id,
        username=current_user.username,
        ip_address=request.client.host if request.client else None,
        details=f"Linked client {client.name} to company {company.legal_name}",
    )
    return db.query(Client).options(joinedload(Client.company)).filter(Client.id == client.id).first()


@router.delete("/{company_id}/members/{client_id}")
def unlink_member(
    company_id: int,
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.name != "admin":
        raise HTTPException(status_code=403, detail="Only admins can unlink company members")
    client = db.query(Client).filter(Client.id == client_id, Client.company_id == company_id).first()
    if client is None:
        raise HTTPException(status_code=404, detail="Company member not found")
    client.company_id = None
    db.commit()
    return {"message": "Member unlinked"}
