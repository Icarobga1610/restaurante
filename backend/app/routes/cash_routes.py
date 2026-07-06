from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from datetime import date, datetime
from app.database import get_db
from app.models.user import User
from app.models.cash_register import CashRegister, CashMovement
from app.schemas.schemas import CashRegisterCreate, CashRegisterOut, CashMovementCreate, CashMovementOut
from app.auth.auth import get_current_user
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/cash", tags=["Cash Register"])

@router.get("/registers", response_model=list[CashRegisterOut])
def list_registers(status: Optional[str] = None, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    q = db.query(CashRegister).options(joinedload(CashRegister.opener), joinedload(CashRegister.closer), joinedload(CashRegister.movements).joinedload(CashMovement.performer))
    if status: q = q.filter(CashRegister.status == status)
    return q.order_by(CashRegister.date.desc()).offset(skip).limit(limit).all()

@router.get("/registers/today")
def get_today_register(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    today = date.today()
    reg = db.query(CashRegister).options(joinedload(CashRegister.movements).joinedload(CashMovement.performer)).filter(CashRegister.date == today).first()
    if not reg: return None
    return reg

@router.post("/registers/open", response_model=CashRegisterOut, status_code=201)
def open_register(data: CashRegisterCreate, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = date.today()
    existing = db.query(CashRegister).filter(CashRegister.date == today).first()
    if existing: raise HTTPException(400, "Register already opened for today")
    reg = CashRegister(date=today, opening_balance=data.opening_balance, opened_by=current_user.id, notes=data.notes)
    db.add(reg); db.commit(); db.refresh(reg)
    AuditService(db).log(action="open", entity_type="cash_register", entity_id=reg.id,
        user_id=current_user.id, username=current_user.username,
        ip_address=request.client.host if request.client else None, details="Cash register opened")
    return reg

@router.post("/registers/{register_id}/movement")
def register_movement(register_id: int, data: CashMovementCreate, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    reg = db.query(CashRegister).filter(CashRegister.id == register_id).first()
    if not reg: raise HTTPException(404, "Register not found")
    if reg.status != "open": raise HTTPException(400, "Register is not open")
    m = CashMovement(cash_register_id=register_id, movement_type=data.movement_type,
        description=data.description, amount=data.amount, payment_method=data.payment_method,
        reference_id=data.reference_id, reference_type=data.reference_type,
        performed_by=current_user.id)
    db.add(m); reg.expected_closing += data.amount; db.commit()
    AuditService(db).log(action="movement", entity_type="cash_movement",
        user_id=current_user.id, username=current_user.username,
        ip_address=request.client.host if request.client else None,
        details=f"Cash movement: {data.movement_type} R$ {data.amount:.2f}")
    return {"message": "Movement registered", "balance": reg.expected_closing}

@router.post("/registers/{register_id}/close")
def close_register(register_id: int, informed_closing: float, notes: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    reg = db.query(CashRegister).filter(CashRegister.id == register_id).first()
    if not reg: raise HTTPException(404, "Register not found")
    if reg.status != "open": raise HTTPException(400, "Register already closed")
    reg.informed_closing = informed_closing
    reg.difference = round(informed_closing - reg.expected_closing, 2)
    reg.status = "closed"; reg.closed_by = current_user.id; reg.closed_at = utcnow()
    if notes: reg.notes = notes
    db.commit()
    return {"message": "Register closed", "expected": reg.expected_closing, "informed": informed_closing, "difference": reg.difference}
