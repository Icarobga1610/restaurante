from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.promotion import Promotion, Coupon, ComboItem, DiscountLog
from app.schemas.schemas import (
    PromotionCreate, PromotionOut,
    CouponCreate, CouponOut, CouponValidateRequest,
    DiscountApplyRequest,
    ComboCreate, ComboItemOut,
    DiscountLogOut,
)
from app.auth.auth import get_current_user
from app.services.promotion_service import PromotionService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/promotions", tags=["Promotions"])


# ── Promotions ─────────────────────────────────────────────────

@router.get("/promotions", response_model=list[PromotionOut])
def list_promotions(
    active_only: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Promotion)
    if active_only:
        query = query.filter(Promotion.active == True)
    return query.order_by(Promotion.created_at.desc()).all()


@router.post("/promotions", response_model=PromotionOut, status_code=201)
def create_promotion(
    data: PromotionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PromotionService(db)
    return service.create_promotion(data.model_dump(), current_user.id, current_user.username)


@router.put("/promotions/{promo_id}/toggle", response_model=PromotionOut)
def toggle_promotion(
    promo_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PromotionService(db)
    try:
        return service.toggle_promotion(promo_id, data.get("active", True), current_user.id, current_user.username)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Coupons ─────────────────────────────────────────────────────

@router.get("/coupons", response_model=list[CouponOut])
def list_coupons(
    active_only: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Coupon)
    if active_only:
        query = query.filter(Coupon.active == True)
    return query.order_by(Coupon.created_at.desc()).all()


@router.post("/coupons", response_model=CouponOut, status_code=201)
def create_coupon(
    data: CouponCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(Coupon).filter(Coupon.code == data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Código de cupom já existe")
    service = PromotionService(db)
    return service.create_coupon(data.model_dump(), current_user.id, current_user.username)


@router.post("/coupons/validate", response_model=dict)
def validate_coupon(
    data: CouponValidateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = PromotionService(db)
    return service.validate_coupon(data.code)


# ── Apply Discount ─────────────────────────────────────────────

@router.post("/apply-discount", response_model=dict)
def apply_discount(
    data: DiscountApplyRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PromotionService(db)

    if data.coupon_code:
        validation = service.validate_coupon(data.coupon_code)
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail=validation.get("error", "Cupom inválido"))
        return service.apply_coupon(
            validation["coupon_id"], data.order_id,
            current_user.id, current_user.username,
        )
    elif data.discount_value and data.reason:
        try:
            return service.apply_manual_discount(
                data.order_id, data.discount_value, data.reason,
                current_user.id, current_user.username,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        raise HTTPException(status_code=400, detail="Informe coupon_code ou discount_value + reason")


# ── Combos ──────────────────────────────────────────────────────

@router.get("/combos/{product_id}", response_model=list[ComboItemOut])
def list_combo_items(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items = db.query(ComboItem).options(
        joinedload(ComboItem.product)
    ).filter(ComboItem.combo_product_id == product_id).all()
    return [
        ComboItemOut(
            id=i.id, combo_product_id=i.combo_product_id,
            product_id=i.product_id,
            product_name=i.product.name if i.product else None,
            quantity=i.quantity, created_at=i.created_at,
        )
        for i in items
    ]


@router.post("/combos", response_model=list[ComboItemOut], status_code=201)
def create_combo(
    data: ComboCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PromotionService(db)
    items = service.create_combo(data.combo_product_id, [i.model_dump() for i in data.items])
    return [
        ComboItemOut(
            id=i.id, combo_product_id=i.combo_product_id,
            product_id=i.product_id,
            product_name=i.product.name if i.product else None,
            quantity=i.quantity, created_at=i.created_at,
        )
        for i in items
    ]


# ── Discount Logs ──────────────────────────────────────────────

@router.get("/discount-logs", response_model=list[DiscountLogOut])
def list_discount_logs(
    order_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(DiscountLog).options(
        joinedload(DiscountLog.user),
        joinedload(DiscountLog.coupon),
        joinedload(DiscountLog.promotion),
    )
    if order_id:
        query = query.filter(DiscountLog.order_id == order_id)
    logs = query.order_by(DiscountLog.created_at.desc()).limit(100).all()
    return [
        DiscountLogOut(
            id=l.id, order_id=l.order_id, user_id=l.user_id,
            user_name=l.user.full_name if l.user else None,
            discount_type=l.discount_type, discount_value=l.discount_value,
            reason=l.reason, coupon_id=l.coupon_id,
            promotion_id=l.promotion_id, created_at=l.created_at,
        )
        for l in logs
    ]
