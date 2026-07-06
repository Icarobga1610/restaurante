from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.internal_consumption import InternalConsumption
from app.schemas.schemas import InternalConsumptionCreate, InternalConsumptionOut
from app.auth.auth import get_current_user
from app.services.internal_consumption_service import InternalConsumptionService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/internal-consumptions", tags=["Internal Consumptions"])


@router.get("", response_model=list[InternalConsumptionOut])
def list_consumptions(
    consumption_type: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(InternalConsumption).options(
        joinedload(InternalConsumption.client),
        joinedload(InternalConsumption.product),
        joinedload(InternalConsumption.authorized_by),
        joinedload(InternalConsumption.created_by),
    )
    if consumption_type:
        query = query.filter(InternalConsumption.consumption_type == consumption_type)
    if month:
        from sqlalchemy import extract
        query = query.filter(extract("month", InternalConsumption.created_at) == month)
    if year:
        from sqlalchemy import extract
        query = query.filter(extract("year", InternalConsumption.created_at) == year)

    records = query.order_by(InternalConsumption.created_at.desc()).offset(skip).limit(limit).all()
    return [
        InternalConsumptionOut(
            id=r.id, consumption_type=r.consumption_type,
            client_id=r.client_id, client_name=r.client.name if r.client else None,
            employee_name=r.employee_name,
            product_id=r.product_id, product_name=r.product.name if r.product else None,
            quantity=r.quantity, estimated_cost=r.estimated_cost,
            reason=r.reason,
            authorized_by_user_id=r.authorized_by_user_id,
            authorized_by_name=r.authorized_by.full_name if r.authorized_by else None,
            created_by_user_id=r.created_by_user_id,
            created_by_name=r.created_by.full_name if r.created_by else None,
            created_at=r.created_at,
        )
        for r in records
    ]


@router.post("", response_model=InternalConsumptionOut, status_code=201)
def create_consumption(
    data: InternalConsumptionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InternalConsumptionService(db)
    try:
        record = service.register(
            data.model_dump(),
            created_by_user_id=current_user.id,
            created_by_username=current_user.username,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    db.refresh(record)
    record = db.query(InternalConsumption).options(
        joinedload(InternalConsumption.client),
        joinedload(InternalConsumption.product),
        joinedload(InternalConsumption.authorized_by),
        joinedload(InternalConsumption.created_by),
    ).filter(InternalConsumption.id == record.id).first()

    return InternalConsumptionOut(
        id=record.id, consumption_type=record.consumption_type,
        client_id=record.client_id, client_name=record.client.name if record.client else None,
        employee_name=record.employee_name,
        product_id=record.product_id, product_name=record.product.name if record.product else None,
        quantity=record.quantity, estimated_cost=record.estimated_cost,
        reason=record.reason,
        authorized_by_user_id=record.authorized_by_user_id,
        authorized_by_name=record.authorized_by.full_name if record.authorized_by else None,
        created_by_user_id=record.created_by_user_id,
        created_by_name=record.created_by.full_name if record.created_by else None,
        created_at=record.created_at,
    )


@router.get("/summary", response_model=dict)
def consumption_summary(
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    from datetime import datetime
from app.utils import utcnow
    from sqlalchemy import extract, func

    now = utcnow()
    month = month or now.month
    year = year or now.year

    total = db.query(func.sum(InternalConsumption.estimated_cost)).filter(
        extract("month", InternalConsumption.created_at) == month,
        extract("year", InternalConsumption.created_at) == year,
    ).scalar() or 0

    by_type = db.query(
        InternalConsumption.consumption_type,
        func.sum(InternalConsumption.estimated_cost).label("total"),
        func.count(InternalConsumption.id).label("count"),
    ).filter(
        extract("month", InternalConsumption.created_at) == month,
        extract("year", InternalConsumption.created_at) == year,
    ).group_by(InternalConsumption.consumption_type).all()

    return {
        "total": round(total, 2),
        "by_type": [
            {"consumption_type": t.consumption_type, "total": round(float(t.total or 0), 2), "count": t.count}
            for t in by_type
        ],
    }
