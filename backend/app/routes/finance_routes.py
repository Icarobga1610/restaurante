from datetime import date, datetime, time
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.auth import get_current_user
from app.database import get_db
from app.models.client import Client
from app.models.expense import Expense
from app.models.monthly_account import MonthlyAccount
from app.models.payment import Payment
from app.models.purchase import Purchase
from app.models.stock_item import StockItem
from app.models.user import User

router = APIRouter(prefix="/api/finance", tags=["Finance"])


def _period_bounds(start_date: date, end_date: date) -> tuple[datetime, datetime]:
    return datetime.combine(start_date, time.min), datetime.combine(end_date, time.max)


@router.get("/ledger")
def get_finance_ledger(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Consolidated cash book for balance analysis."""
    if current_user.role.name not in ("admin", "financial"):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Only admin/financial can view finance ledger")

    start_dt, end_dt = _period_bounds(start_date, end_date)

    entries = []

    payments = (
        db.query(Payment)
        .filter(Payment.paid_at >= start_dt, Payment.paid_at <= end_dt)
        .all()
    )
    for payment in payments:
        client_name = payment.client.name if payment.client else f"Cliente #{payment.client_id}"
        entries.append({
            "date": payment.paid_at.isoformat(),
            "kind": "entrada",
            "category": "conta_recebida",
            "description": f"Recebimento de conta mensal - {client_name}",
            "amount": round(float(payment.amount or 0), 2),
            "reference_type": "payment",
            "reference_id": payment.id,
            "payment_method": payment.payment_method,
        })

    expenses = (
        db.query(Expense)
        .filter(Expense.expense_date >= start_date, Expense.expense_date <= end_date)
        .all()
    )
    for expense in expenses:
        entries.append({
            "date": expense.expense_date.isoformat(),
            "kind": "saida",
            "category": f"despesa_{expense.category}",
            "description": expense.description,
            "amount": round(-abs(float(expense.amount or 0)), 2),
            "reference_type": "expense",
            "reference_id": expense.id,
            "payment_method": expense.payment_method,
        })

    purchases = (
        db.query(Purchase)
        .filter(Purchase.purchase_date >= start_dt, Purchase.purchase_date <= end_dt)
        .filter(Purchase.status == "received")
        .all()
    )
    for purchase in purchases:
        entries.append({
            "date": purchase.purchase_date.isoformat(),
            "kind": "saida",
            "category": "compra_estoque",
            "description": f"Compra de estoque{f' NF {purchase.invoice_number}' if purchase.invoice_number else ''}",
            "amount": round(-abs(float(purchase.total_cost or 0)), 2),
            "reference_type": "purchase",
            "reference_id": purchase.id,
            "payment_method": purchase.payment_method,
        })

    receivables_query = (
        db.query(MonthlyAccount)
        .filter(MonthlyAccount.status.in_(["open", "closed", "confirmed_by_biometrics", "overdue"]))
    )
    receivables_in_period = receivables_query.filter(
        MonthlyAccount.due_date >= start_date,
        MonthlyAccount.due_date <= end_date,
    ).all()
    for account in receivables_in_period:
        client_name = account.client.name if account.client else f"Cliente #{account.client_id}"
        entries.append({
            "date": account.due_date.isoformat() if account.due_date else f"{account.year}-{account.month:02d}-01",
            "kind": "receber",
            "category": "conta_a_receber",
            "description": f"Conta a receber - {client_name} ({account.month:02d}/{account.year})",
            "amount": round(float(account.total or 0), 2),
            "reference_type": "monthly_account",
            "reference_id": account.id,
            "payment_method": None,
        })

    entries.sort(key=lambda item: item["date"], reverse=True)

    received_total = sum(float(payment.amount or 0) for payment in payments)
    expenses_total = sum(float(expense.amount or 0) for expense in expenses)
    purchases_total = sum(float(purchase.total_cost or 0) for purchase in purchases)
    receivable_total = sum(float(account.total or 0) for account in receivables_in_period)
    receivable_total_all = sum(float(account.total or 0) for account in receivables_query.all())

    stock_items = db.query(StockItem).filter(StockItem.status == "active").all()
    stock_value = sum(
        float(item.current_quantity or 0) * float(item.average_cost or item.unit_cost or 0)
        for item in stock_items
    )

    return {
        "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
        "summary": {
            "received_total": round(received_total, 2),
            "receivable_total": round(receivable_total, 2),
            "receivable_total_all": round(receivable_total_all, 2),
            "expenses_total": round(expenses_total, 2),
            "stock_purchases_total": round(purchases_total, 2),
            "outflow_total": round(expenses_total + purchases_total, 2),
            "cash_result": round(received_total - expenses_total - purchases_total, 2),
            "projected_result": round(received_total + receivable_total - expenses_total - purchases_total, 2),
            "stock_value": round(stock_value, 2),
        },
        "entries": entries,
    }
