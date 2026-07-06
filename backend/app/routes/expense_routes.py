from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from datetime import date
from app.database import get_db
from app.models.user import User
from app.models.expense import Expense
from app.schemas.schemas import ExpenseCreate, ExpenseOut
from app.auth.auth import get_current_user
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/expenses", tags=["Expenses"])

@router.get("", response_model=list[ExpenseOut])
def list_expenses(
    category: Optional[str] = None, supplier_id: Optional[int] = None,
    start_date: Optional[date] = None, end_date: Optional[date] = None,
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db), _: User = Depends(get_current_user),
):
    q = db.query(Expense).options(joinedload(Expense.supplier), joinedload(Expense.creator))
    if category: q = q.filter(Expense.category == category)
    if supplier_id: q = q.filter(Expense.supplier_id == supplier_id)
    if start_date: q = q.filter(Expense.expense_date >= start_date)
    if end_date: q = q.filter(Expense.expense_date <= end_date)
    exps = q.order_by(Expense.expense_date.desc()).offset(skip).limit(limit).all()
    return [ExpenseOut(id=e.id, description=e.description, category=e.category, amount=e.amount,
        expense_date=e.expense_date, payment_method=e.payment_method,
        supplier_id=e.supplier_id, supplier_name=e.supplier.name if e.supplier else None,
        notes=e.notes, created_by=e.created_by,
        creator_name=e.creator.full_name if e.creator else None, created_at=e.created_at) for e in exps]

@router.post("", response_model=ExpenseOut, status_code=201)
def create_expense(data: ExpenseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role.name not in ("admin", "financial"): raise HTTPException(403, "Insufficient permissions")
    expense = Expense(**data.model_dump(), created_by=current_user.id)
    db.add(expense); db.commit(); db.refresh(expense)
    AuditService(db).log(action="create", entity_type="expense", entity_id=expense.id,
        user_id=current_user.id, username=current_user.username,
        details=f"Expense: {expense.description} R$ {expense.amount:.2f}")
    return expense

@router.get("/categories")
def list_expense_categories():
    return {"categories": ["aluguel", "energia", "agua", "internet", "salarios", "manutencao",
        "compra_emergencial", "marketing", "imposto", "fornecedores", "outros"]}

@router.get("/summary")
def get_expense_summary(start_date: date, end_date: date, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    from sqlalchemy import func
    rows = db.query(Expense.category, func.sum(Expense.amount).label("total")).filter(
        Expense.expense_date >= start_date, Expense.expense_date <= end_date
    ).group_by(Expense.category).all()
    total = sum(r.total for r in rows)
    return {"total": round(float(total), 2), "by_category": [{"category": r.category, "total": round(float(r.total), 2)} for r in rows],
        "start_date": str(start_date), "end_date": str(end_date)}
