from datetime import datetime
from app.utils import utcnow, date
from collections import defaultdict
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.models.order import Order, OrderItem
from app.models.client import Client
from app.models.product import Product
from app.models.monthly_account import MonthlyAccount
from app.models.insight import SeasonalityMetric, InsightLog


class InsightService:
    def __init__(self, db: Session):
        self.db = db

    def calculate_top_products_by_day(self) -> List[Dict]:
        """Products most sold by day of week."""
        results = (
            self.db.query(
                func.to_char(Order.created_at, 'D').label("day_of_week"),
                OrderItem.product_id,
                OrderItem.product_name,
                func.sum(OrderItem.quantity).label("total_qty"),
                func.sum(OrderItem.total).label("total_revenue"),
            )
            .join(OrderItem, OrderItem.order_id == Order.id)
            .filter(Order.status.in_(["confirmed", "invoiced", "paid"]))
            .group_by("day_of_week", OrderItem.product_id, OrderItem.product_name)
            .order_by("day_of_week", func.sum(OrderItem.quantity).desc())
            .all()
        )

        days = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
        by_day = defaultdict(list)
        for row in results:
            raw_day = int(row.day_of_week) if row.day_of_week is not None else None
            idx = (raw_day + 6) % 7 if raw_day is not None else -1
            day_name = days[idx] if idx >= 0 else "Desconhecido"
            by_day[day_name].append({
                "product_id": row.product_id,
                "product_name": row.product_name,
                "total_quantity": float(row.total_qty),
                "total_revenue": float(row.total_revenue),
            })

        metric = []
        for day, products in by_day.items():
            metric.append({"day": day, "products": products[:10]})

        # Save metric
        self._save_metric("top_products_day", "day", metric)

        return metric

    def calculate_top_products_by_month(self) -> List[Dict]:
        """Products most sold by month."""
        results = (
            self.db.query(
                func.to_char(Order.created_at, 'YYYY-MM').label("month"),
                OrderItem.product_id,
                OrderItem.product_name,
                func.sum(OrderItem.quantity).label("total_qty"),
                func.sum(OrderItem.total).label("total_revenue"),
            )
            .join(OrderItem, OrderItem.order_id == Order.id)
            .filter(Order.status.in_(["confirmed", "invoiced", "paid"]))
            .group_by("month", OrderItem.product_id, OrderItem.product_name)
            .order_by("month", func.sum(OrderItem.quantity).desc())
            .all()
        )

        by_month = defaultdict(list)
        for row in results:
            by_month[row.month].append({
                "product_id": row.product_id,
                "product_name": row.product_name,
                "total_quantity": float(row.total_qty),
                "total_revenue": float(row.total_revenue),
            })

        metric = [{"month": m, "products": prods[:10]} for m, prods in by_month.items()]
        self._save_metric("top_products_month", "month", metric)
        return metric

    def calculate_peak_hours(self) -> List[Dict]:
        """Peak hours of movement."""
        results = (
            self.db.query(
                func.to_char(Order.created_at, 'HH').label("hour"),
                func.count(Order.id).label("order_count"),
                func.sum(Order.total).label("total_revenue"),
            )
            .filter(Order.status.in_(["confirmed", "invoiced", "paid"]))
            .group_by("hour")
            .order_by(func.count(Order.id).desc())
            .all()
        )

        metric = [
            {
                "hour": f"{int(row.hour):02d}:00",
                "order_count": row.order_count,
                "total_revenue": float(row.total_revenue or 0),
            }
            for row in results
        ]
        self._save_metric("peak_hours", "hour", metric)
        return metric

    def calculate_top_clients(self) -> List[Dict]:
        """Clients with highest consumption."""
        results = (
            self.db.query(
                Client.id,
                Client.name,
                func.count(Order.id).label("order_count"),
                func.sum(Order.total).label("total_consumed"),
            )
            .join(Order, Order.client_id == Client.id)
            .filter(Order.status.in_(["confirmed", "invoiced", "paid"]))
            .group_by(Client.id, Client.name)
            .order_by(func.sum(Order.total).desc())
            .limit(20)
            .all()
        )

        metric = [
            {
                "client_id": row.id,
                "client_name": row.name,
                "order_count": row.order_count,
                "total_consumed": float(row.total_consumed or 0),
            }
            for row in results
        ]
        self._save_metric("top_clients", "all", metric)
        return metric

    def calculate_category_consumption(self) -> List[Dict]:
        """Consumption by category."""
        results = (
            self.db.query(
                Product.category,
                func.count(OrderItem.id).label("item_count"),
                func.sum(OrderItem.total).label("total_revenue"),
            )
            .join(OrderItem, OrderItem.product_id == Product.id)
            .join(Order, Order.id == OrderItem.order_id)
            .filter(Order.status.in_(["confirmed", "invoiced", "paid"]))
            .group_by(Product.category)
            .order_by(func.sum(OrderItem.total).desc())
            .all()
        )

        metric = [
            {
                "category": row.category,
                "item_count": row.item_count,
                "total_revenue": float(row.total_revenue or 0),
            }
            for row in results
        ]
        self._save_metric("category_consumption", "all", metric)
        return metric

    def generate_insights(self) -> List[Dict[str, Any]]:
        """Generate business insights based on data analysis."""
        insights = []

        # Check top products by day insight
        top_by_day = self.calculate_top_products_by_day()
        for day_data in top_by_day:
            if day_data["products"]:
                top = day_data["products"][0]
                insights.append({
                    "type": "product_day_pattern",
                    "title": f"{top['product_name']} vende mais às {day_data['day']}",
                    "description": f"Produto {top['product_name']} é o mais vendido às {day_data['day']}s com {top['total_quantity']:.0f} unidades.",
                    "severity": "info",
                    "data": {"day": day_data["day"], "product": top},
                })

        # Peak hours insight
        peak_hours = self.calculate_peak_hours()
        if peak_hours:
            top_hours = peak_hours[:3]
            hour_ranges = ", ".join([h["hour"] for h in top_hours])
            insights.append({
                "type": "peak_hours",
                "title": f"Horários de maior movimento: {hour_ranges}",
                "description": f"Os horários com maior volume de pedidos são {hour_ranges}.",
                "severity": "info",
                "data": {"peak_hours": top_hours},
            })

        # Top clients insight
        top_clients = self.calculate_top_clients()
        if top_clients:
            c = top_clients[0]
            insights.append({
                "type": "top_client",
                "title": f"{c['client_name']} é o cliente com maior consumo",
                "description": f"{c['client_name']} consumiu R$ {c['total_consumed']:.2f} no total.",
                "severity": "info",
                "data": c,
            })

        # Overdue accounts
        now = utcnow()
        overdue = (
            self.db.query(MonthlyAccount)
            .filter(
                MonthlyAccount.status == "closed",
                MonthlyAccount.month < now.month,
                MonthlyAccount.year <= now.year,
            )
            .count()
        )
        if overdue > 0:
            insights.append({
                "type": "overdue_accounts",
                "title": f"Há {overdue} conta(s) vencida(s) acima de R$ 0",
                "description": f"Existem {overdue} contas mensais fechadas mas não pagas de meses anteriores.",
                "severity": "warning",
                "data": {"count": overdue},
            })

        # Accounts closed but not yet confirmed by fingerprint.
        unsigned = (
            self.db.query(MonthlyAccount)
            .filter(MonthlyAccount.status == "closed", MonthlyAccount.biometric_verification_id.is_(None))
            .count()
        )
        if unsigned > 0:
            insights.append({
                "type": "unsigned_accounts",
                "title": f"{unsigned} conta(s) fechada(s) sem biometria",
                "description": f"Existem {unsigned} contas mensais fechadas que ainda não foram confirmadas por digital.",
                "severity": "warning",
                "data": {"count": unsigned},
            })

        # Month comparison (current vs previous)
        current_month = now.month
        current_year = now.year
        prev_month = current_month - 1 if current_month > 1 else 12
        prev_year = current_year if current_month > 1 else current_year - 1

        current_total = (
            self.db.query(func.sum(MonthlyAccount.total))
            .filter(MonthlyAccount.month == current_month, MonthlyAccount.year == current_year)
            .scalar() or 0
        )
        prev_total = (
            self.db.query(func.sum(MonthlyAccount.total))
            .filter(MonthlyAccount.month == prev_month, MonthlyAccount.year == prev_year)
            .scalar() or 0
        )

        if prev_total > 0:
            change_pct = ((current_total - prev_total) / prev_total) * 100
            if abs(change_pct) > 10:
                direction = "aumento" if change_pct > 0 else "queda"
                insights.append({
                    "type": "month_comparison",
                    "title": f"{direction.capitalize()} de {abs(change_pct):.1f}% no faturamento mensal",
                    "description": f"Comparado ao mês anterior, o faturamento teve {direction} de {abs(change_pct):.1f}% (atual: R$ {current_total:.2f}, anterior: R$ {prev_total:.2f}).",
                    "severity": "info" if change_pct > 0 else "warning",
                    "data": {"current_total": current_total, "prev_total": prev_total, "change_pct": change_pct},
                })

        # Products near monthly limit
        near_limit_clients = (
            self.db.query(Client)
            .filter(
                Client.monthly_limit.isnot(None),
                Client.status == "active",
            )
            .all()
        )
        for client in near_limit_clients:
            consumed = (
                self.db.query(func.sum(Order.total))
                .filter(
                    Order.client_id == client.id,
                    func.to_char(Order.created_at, 'YYYY-MM') == f"{current_year}-{current_month:02d}",
                    Order.status.in_(["confirmed", "invoiced"]),
                )
                .scalar() or 0
            )
            if consumed > 0 and client.monthly_limit and consumed >= client.monthly_limit * 0.9:
                insights.append({
                    "type": "near_limit",
                    "title": f"{client.name} está próximo do limite mensal",
                    "description": f"{client.name} consumiu R$ {consumed:.2f} de R$ {client.monthly_limit:.2f} ({consumed/client.monthly_limit*100:.1f}%).",
                    "severity": "alert",
                    "data": {"client_id": client.id, "client_name": client.name, "consumed": consumed, "limit": client.monthly_limit},
                })

        # Falling product demand
        current_products = (
            self.db.query(
                OrderItem.product_id,
                OrderItem.product_name,
                func.sum(OrderItem.quantity).label("qty"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .filter(
                func.to_char(Order.created_at, 'YYYY-MM') == f"{current_year}-{current_month:02d}",
                Order.status.in_(["confirmed", "invoiced", "paid"]),
            )
            .group_by(OrderItem.product_id, OrderItem.product_name)
            .all()
        )
        prev_products = {
            row.product_id: row.qty
            for row in (
                self.db.query(
                    OrderItem.product_id,
                    func.sum(OrderItem.quantity).label("qty"),
                )
                .join(Order, Order.id == OrderItem.order_id)
                .filter(
                    func.to_char(Order.created_at, 'YYYY-MM') == f"{prev_year}-{prev_month:02d}",
                    Order.status.in_(["confirmed", "invoiced", "paid"]),
                )
                .group_by(OrderItem.product_id)
                .all()
            )
        }

        for row in current_products:
            prev_qty = prev_products.get(row.product_id, 0)
            if prev_qty > 0:
                change = ((row.qty - prev_qty) / prev_qty) * 100
                if change < -30:
                    insights.append({
                        "type": "falling_demand",
                        "title": f"{row.product_name} está com queda de consumo",
                        "description": f"{row.product_name} teve queda de {abs(change):.1f}% no consumo comparado ao mês anterior.",
                        "severity": "warning",
                        "data": {"product_id": row.product_id, "product_name": row.product_name, "change_pct": change},
                    })
                elif change > 50:
                    insights.append({
                        "type": "rising_demand",
                        "title": f"{row.product_name} está com demanda crescente",
                        "description": f"{row.product_name} teve aumento de {change:.1f}% no consumo comparado ao mês anterior.",
                        "severity": "info",
                        "data": {"product_id": row.product_id, "product_name": row.product_name, "change_pct": change},
                    })

        # Save insights
        for ins in insights:
            existing = (
                self.db.query(InsightLog)
                .filter(InsightLog.insight_type == ins["type"], InsightLog.is_active == 1)
                .first()
            )
            if existing:
                existing.is_active = 0
            new_insight = InsightLog(
                insight_type=ins["type"],
                title=ins["title"],
                description=ins["description"],
                severity=ins["severity"],
                data=ins.get("data"),
            )
            self.db.add(new_insight)

        self.db.commit()
        return insights

    def _save_metric(self, metric_type: str, period: str, data: list):
        metric = SeasonalityMetric(
            metric_type=metric_type,
            period=period,
            data=data,
        )
        self.db.add(metric)
        self.db.commit()

    def get_active_insights(self) -> List[InsightLog]:
        return (
            self.db.query(InsightLog)
            .filter(InsightLog.is_active == 1)
            .order_by(InsightLog.created_at.desc())
            .all()
        )
