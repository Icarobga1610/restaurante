from datetime import datetime
from app.utils import utcnow
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, cast, String
from sqlalchemy.sql import text

from app.database import get_db, engine
from app.models.user import User
from app.models.client import Client
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.monthly_account import MonthlyAccount
from app.models.payment import Payment
from app.schemas.schemas import DashboardData
from app.auth.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardData)
def get_dashboard(
    month: int = Query(default=None),
    year: int = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    now = utcnow()
    month = month or now.month
    year = year or now.year

    data = DashboardData()

    # Total revenue from monthly accounts
    total_open = (
        db.query(func.sum(MonthlyAccount.total))
        .filter(MonthlyAccount.month == month, MonthlyAccount.year == year)
        .scalar() or 0
    )
    data.month_revenue_open = round(total_open, 2)

    # Total paid
    total_paid = (
        db.query(func.sum(Payment.amount))
        .join(MonthlyAccount, Payment.monthly_account_id == MonthlyAccount.id)
        .filter(MonthlyAccount.month == month, MonthlyAccount.year == year)
        .scalar() or 0
    )
    data.month_revenue_paid = round(total_paid, 2)
    data.month_revenue_pending = round(total_open - total_paid, 2)

    # Active clients
    data.active_clients = db.query(Client).filter(Client.status == "active").count()

    # Products
    data.total_products = db.query(Product).filter(Product.is_active == True).count()

    # Orders month
    data.total_orders_month = (
        db.query(Order)
        .filter(
            extract("month", Order.created_at) == month,
            extract("year", Order.created_at) == year,
            Order.status.in_(["confirmed", "invoiced", "paid"]),
        )
        .count()
    )

    # Top clients
    top_clients = (
        db.query(
            Client.id,
            Client.name,
            func.count(Order.id).label("order_count"),
            func.sum(Order.total).label("total"),
        )
        .join(Order, Order.client_id == Client.id)
        .filter(
            extract("month", Order.created_at) == month,
            extract("year", Order.created_at) == year,
            Order.status.in_(["confirmed", "invoiced", "paid"]),
        )
        .group_by(Client.id, Client.name)
        .order_by(func.sum(Order.total).desc())
        .limit(10)
        .all()
    )
    data.top_clients = [
        {"id": c.id, "name": c.name, "order_count": c.order_count, "total": round(float(c.total or 0), 2)}
        for c in top_clients
    ]

    # Top products
    top_products = (
        db.query(
            Product.id,
            Product.name,
            func.sum(OrderItem.quantity).label("qty"),
            func.sum(OrderItem.total).label("total"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, OrderItem.order_id == Order.id)
        .filter(
            extract("month", Order.created_at) == month,
            extract("year", Order.created_at) == year,
            Order.status.in_(["confirmed", "invoiced", "paid"]),
        )
        .group_by(Product.id, Product.name)
        .order_by(func.sum(OrderItem.total).desc())
        .limit(10)
        .all()
    )
    data.top_products = [
        {"id": p.id, "name": p.name, "quantity": float(p.qty or 0), "total": round(float(p.total or 0), 2)}
        for p in top_products
    ]

    # Average ticket
    avg_ticket = (
        db.query(func.avg(Order.total))
        .filter(
            extract("month", Order.created_at) == month,
            extract("year", Order.created_at) == year,
            Order.status.in_(["confirmed", "invoiced", "paid"]),
        )
        .scalar()
    )
    data.average_ticket = round(float(avg_ticket or 0), 2)

    # Consumption by day (works on both SQLite and PostgreSQL)
    is_postgres = engine.dialect.name == "postgresql"
    day_expr = (
        func.to_char(Order.created_at, "DD/MM")
        if is_postgres
        else func.strftime("%d/%m", Order.created_at)
    )
    consumption_by_day = (
        db.query(
            day_expr.label("day"),
            func.sum(Order.total).label("total"),
        )
        .filter(
            extract("month", Order.created_at) == month,
            extract("year", Order.created_at) == year,
            Order.status.in_(["confirmed", "invoiced", "paid"]),
        )
        .group_by(day_expr)
        .order_by(func.min(Order.created_at))
        .all()
    )
    data.consumption_by_day = [
        {"day": d.day, "total": round(float(d.total or 0), 2)}
        for d in consumption_by_day
    ]

    # Consumption by category
    consumption_by_category = (
        db.query(
            Product.category,
            func.sum(OrderItem.total).label("total"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, OrderItem.order_id == Order.id)
        .filter(
            extract("month", Order.created_at) == month,
            extract("year", Order.created_at) == year,
            Order.status.in_(["confirmed", "invoiced", "paid"]),
        )
        .group_by(Product.category)
        .order_by(func.sum(OrderItem.total).desc())
        .all()
    )
    data.consumption_by_category = [
        {"category": c.category, "total": round(float(c.total or 0), 2)}
        for c in consumption_by_category
    ]

    # Overdue accounts (closed accounts from previous months not paid)
    data.overdue_accounts = (
        db.query(MonthlyAccount)
        .filter(
            MonthlyAccount.status == "closed",
            MonthlyAccount.month < month,
        )
        .count()
    )

    # Unverified accounts (closed but not yet confirmed by biometrics)
    data.unsigned_accounts = (
        db.query(MonthlyAccount)
        .filter(
            MonthlyAccount.status == "closed",
            MonthlyAccount.biometric_verification_id.is_(None),
        )
        .count()
    )

    return data