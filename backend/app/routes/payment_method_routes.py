from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.auth import get_current_user
from app.database import get_db
from app.models.payment_method import PaymentMethod
from app.models.user import User
from app.schemas.schemas import PaymentMethodCreate, PaymentMethodOut, PaymentMethodUpdate

router = APIRouter(prefix="/api/payment-methods", tags=["Payment Methods"])


def _normalize_code(code: str) -> str:
    return code.strip().lower().replace(" ", "_")


def _ensure_seed(db: Session) -> None:
    if db.query(PaymentMethod).count() > 0:
        return
    defaults = [
        PaymentMethod(code="pix", name="Pix", is_default=True),
        PaymentMethod(code="cash", name="Dinheiro"),
        PaymentMethod(code="debit", name="Cartão de Débito"),
        PaymentMethod(code="credit", name="Cartão de Crédito"),
        PaymentMethod(code="transfer", name="Transferência"),
    ]
    db.add_all(defaults)
    db.commit()


def _clear_default(db: Session) -> None:
    db.query(PaymentMethod).update({PaymentMethod.is_default: False})


@router.get("", response_model=list[PaymentMethodOut])
def list_payment_methods(
    active_only: bool = True,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    _ensure_seed(db)
    query = db.query(PaymentMethod)
    if active_only:
        query = query.filter(PaymentMethod.is_active == True)
    return query.order_by(PaymentMethod.is_default.desc(), PaymentMethod.name.asc()).all()


@router.get("/default", response_model=PaymentMethodOut)
def get_default_payment_method(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    _ensure_seed(db)
    method = db.query(PaymentMethod).filter(PaymentMethod.is_default == True, PaymentMethod.is_active == True).first()
    if not method:
        method = db.query(PaymentMethod).filter(PaymentMethod.is_active == True).order_by(PaymentMethod.name.asc()).first()
    if not method:
        raise HTTPException(status_code=404, detail="Nenhuma forma de pagamento ativa")
    return method


@router.post("", response_model=PaymentMethodOut, status_code=201)
def create_payment_method(
    data: PaymentMethodCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.name not in ("admin", "financial"):
        raise HTTPException(status_code=403, detail="Only admin/financial can manage payment methods")
    code = _normalize_code(data.code)
    if db.query(PaymentMethod).filter(PaymentMethod.code == code).first():
        raise HTTPException(status_code=400, detail="Forma de pagamento já existe")
    if data.is_default:
        _clear_default(db)
    method = PaymentMethod(code=code, name=data.name.strip(), is_default=data.is_default, is_active=data.is_active)
    db.add(method)
    db.commit()
    db.refresh(method)
    return method


@router.put("/{method_id}", response_model=PaymentMethodOut)
def update_payment_method(
    method_id: int,
    data: PaymentMethodUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.name not in ("admin", "financial"):
        raise HTTPException(status_code=403, detail="Only admin/financial can manage payment methods")
    method = db.query(PaymentMethod).filter(PaymentMethod.id == method_id).first()
    if not method:
        raise HTTPException(status_code=404, detail="Forma de pagamento não encontrada")
    payload = data.model_dump(exclude_unset=True)
    if "code" in payload and payload["code"]:
        code = _normalize_code(payload["code"])
        existing = db.query(PaymentMethod).filter(PaymentMethod.code == code, PaymentMethod.id != method_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Forma de pagamento já existe")
        method.code = code
    if "name" in payload and payload["name"]:
        method.name = payload["name"].strip()
    if "is_active" in payload:
        method.is_active = payload["is_active"]
    if payload.get("is_default") is True:
        _clear_default(db)
        method.is_default = True
        method.is_active = True
    elif payload.get("is_default") is False:
        method.is_default = False
    db.commit()
    db.refresh(method)
    return method


@router.post("/{method_id}/default", response_model=PaymentMethodOut)
def set_default_payment_method(
    method_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.name not in ("admin", "financial"):
        raise HTTPException(status_code=403, detail="Only admin/financial can manage payment methods")
    method = db.query(PaymentMethod).filter(PaymentMethod.id == method_id).first()
    if not method:
        raise HTTPException(status_code=404, detail="Forma de pagamento não encontrada")
    _clear_default(db)
    method.is_default = True
    method.is_active = True
    db.commit()
    db.refresh(method)
    return method
