from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.loss_record import LossRecord
from app.schemas.schemas import LossRecordCreate, LossRecordOut
from app.auth.auth import get_current_user
from app.services.loss_service import LossService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/losses", tags=["Losses"])


@router.get("", response_model=list[LossRecordOut])
def list_losses(
    loss_type: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(LossRecord).options(
        joinedload(LossRecord.stock_item),
        joinedload(LossRecord.product),
        joinedload(LossRecord.user),
    )
    if loss_type:
        query = query.filter(LossRecord.loss_type == loss_type)
    if month:
        from sqlalchemy import extract
        query = query.filter(extract("month", LossRecord.created_at) == month)
    if year:
        from sqlalchemy import extract
        query = query.filter(extract("year", LossRecord.created_at) == year)

    records = query.order_by(LossRecord.created_at.desc()).offset(skip).limit(limit).all()
    return [
        LossRecordOut(
            id=r.id,
            stock_item_id=r.stock_item_id,
            stock_item_name=r.stock_item.name if r.stock_item else None,
            product_id=r.product_id,
            product_name=r.product.name if r.product else None,
            quantity=r.quantity, unit_measure=r.unit_measure,
            estimated_cost=r.estimated_cost, loss_type=r.loss_type,
            reason=r.reason, user_id=r.user_id,
            user_name=r.user.full_name if r.user else None,
            created_at=r.created_at,
        )
        for r in records
    ]


@router.post("", response_model=LossRecordOut, status_code=201)
def create_loss(
    data: LossRecordCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = LossService(db)
    try:
        record = service.register_loss(
            data.model_dump(),
            user_id=current_user.id,
            username=current_user.username,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    db.refresh(record)
    # Reload with relationships
    record = db.query(LossRecord).options(
        joinedload(LossRecord.stock_item),
        joinedload(LossRecord.product),
        joinedload(LossRecord.user),
    ).filter(LossRecord.id == record.id).first()

    return LossRecordOut(
        id=record.id,
        stock_item_id=record.stock_item_id,
        stock_item_name=record.stock_item.name if record.stock_item else None,
        product_id=record.product_id,
        product_name=record.product.name if record.product else None,
        quantity=record.quantity, unit_measure=record.unit_measure,
        estimated_cost=record.estimated_cost, loss_type=record.loss_type,
        reason=record.reason, user_id=record.user_id,
        user_name=record.user.full_name if record.user else None,
        created_at=record.created_at,
    )


@router.get("/summary", response_model=dict)
def loss_summary(
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

    total_losses = db.query(func.sum(LossRecord.estimated_cost)).filter(
        extract("month", LossRecord.created_at) == month,
        extract("year", LossRecord.created_at) == year,
    ).scalar() or 0

    by_type = db.query(
        LossRecord.loss_type,
        func.sum(LossRecord.estimated_cost).label("total"),
        func.count(LossRecord.id).label("count"),
    ).filter(
        extract("month", LossRecord.created_at) == month,
        extract("year", LossRecord.created_at) == year,
    ).group_by(LossRecord.loss_type).all()

    return {
        "total": round(total_losses, 2),
        "by_type": [
            {"loss_type": t.loss_type, "total": round(float(t.total or 0), 2), "count": t.count}
            for t in by_type
        ],
    }
