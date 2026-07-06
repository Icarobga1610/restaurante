"""Stock Service — inventory management and auto-deduction for product sales."""

from datetime import datetime, date, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.stock_item import StockItem
from app.models.stock_movement import StockMovement
from app.models.product_recipe import ProductRecipe, ProductRecipeItem
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.services.audit_service import AuditService


class StockService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    # ── Recipe Cost Calculation ─────────────────────────────────

    def calculate_recipe_cost(self, recipe_id: int) -> Tuple[float, float]:
        """Calculate total cost and estimated margin for a product recipe."""
        items = self.db.query(ProductRecipeItem).filter(
            ProductRecipeItem.recipe_id == recipe_id
        ).all()

        total_cost = 0.0
        for item in items:
            stock = self.db.query(StockItem).filter(
                StockItem.id == item.stock_item_id
            ).first()
            if stock:
                # Use average cost for calculation
                cost_price = stock.average_cost or stock.unit_cost
                item.cost = round(cost_price * item.quantity_required, 4)
                total_cost += item.cost

        # Update recipe total cost
        recipe = self.db.query(ProductRecipe).filter(
            ProductRecipe.id == recipe_id
        ).first()
        if recipe:
            recipe.total_cost = round(total_cost, 2)
            # Calculate margin
            product = self.db.query(Product).filter(
                Product.id == recipe.product_id
            ).first()
            if product and product.price > 0:
                recipe.estimated_margin = round(
                    ((product.price - total_cost) / product.price) * 100, 2
                )
                # Update product estimated cost
                product.estimated_cost = round(total_cost, 2)
                product.estimated_margin = recipe.estimated_margin

        self.db.commit()
        return (round(total_cost, 2), recipe.estimated_margin or 0)

    # ── Auto-Deduct Stock on Order ─────────────────────────────

    def deduct_stock_for_order(self, order_id: int) -> List[str]:
        """Automatically deduct stock for all items in a confirmed order.

        Returns a list of alerts for insufficient stock items.
        """
        alerts = []
        items = self.db.query(OrderItem).filter(
            OrderItem.order_id == order_id
        ).all()

        for item in items:
            recipe = self.db.query(ProductRecipe).filter(
                ProductRecipe.product_id == item.product_id
            ).first()
            if not recipe:
                continue  # No recipe for this product

            recipe_items = self.db.query(ProductRecipeItem).filter(
                ProductRecipeItem.recipe_id == recipe.id
            ).all()

            for ri in recipe_items:
                stock = self.db.query(StockItem).filter(
                    StockItem.id == ri.stock_item_id
                ).first()
                if not stock:
                    continue

                # Calculate total quantity needed
                needed = ri.quantity_required * item.quantity

                # Check if we have enough
                if stock.current_quantity < needed:
                    alerts.append(
                        f"Insumo '{stock.name}' insuficiente para '{item.product_name}'. "
                        f"Tem {stock.current_quantity:.2f} {stock.unit_measure}, "
                        f"precisa de {needed:.2f}"
                    )
                    continue

                # Deduct
                stock.current_quantity -= needed

                # Record movement
                movement = StockMovement(
                    stock_item_id=stock.id,
                    movement_type="saida_venda",
                    quantity=-needed,
                    unit_cost=stock.average_cost or stock.unit_cost,
                    total_cost=(stock.average_cost or stock.unit_cost) * needed,
                    reference_id=order_id,
                    reference_type="order",
                )
                self.db.add(movement)

                # Low stock alert
                if stock.current_quantity <= stock.minimum_stock:
                    alerts.append(
                        f"Estoque baixo: '{stock.name}' "
                        f"({stock.current_quantity:.2f} {stock.unit_measure} / "
                        f"mínimo {stock.minimum_stock:.2f})"
                    )

        self.db.commit()
        return alerts

    # ── Stock Entry (Purchase Receiving) ─────────────────────

    def receive_stock(
        self,
        stock_item_id: int,
        quantity: float,
        unit_cost: float,
        reference_id: Optional[int] = None,
        reference_type: str = "purchase",
        notes: Optional[str] = None,
        performed_by: Optional[int] = None,
    ) -> StockItem:
        """Register stock entry and update average cost."""
        stock = self.db.query(StockItem).filter(
            StockItem.id == stock_item_id
        ).first()
        if not stock:
            raise ValueError(f"Stock item #{stock_item_id} not found")

        # Calculate new average cost
        old_total = stock.current_quantity * stock.average_cost
        new_total = quantity * unit_cost
        new_qty = stock.current_quantity + quantity

        if new_qty > 0:
            stock.average_cost = round((old_total + new_total) / new_qty, 4)
        else:
            stock.average_cost = unit_cost

        stock.current_quantity = new_qty
        stock.unit_cost = unit_cost  # Update latest unit cost

        # Record movement
        movement = StockMovement(
            stock_item_id=stock.id,
            movement_type="entrada_compra",
            quantity=quantity,
            unit_cost=unit_cost,
            total_cost=quantity * unit_cost,
            reference_id=reference_id,
            reference_type=reference_type,
            notes=notes,
            performed_by=performed_by,
        )
        self.db.add(movement)
        self.db.commit()
        self.db.refresh(stock)
        return stock

    # ── Manual Stock Adjustment ───────────────────────────────

    def adjust_stock(
        self,
        stock_item_id: int,
        new_quantity: float,
        reason: str = "ajuste_manual",
        notes: Optional[str] = None,
        performed_by: Optional[int] = None,
    ) -> StockItem:
        """Manually adjust stock quantity."""
        stock = self.db.query(StockItem).filter(
            StockItem.id == stock_item_id
        ).first()
        if not stock:
            raise ValueError(f"Stock item #{stock_item_id} not found")

        diff = new_quantity - stock.current_quantity

        if diff != 0:
            movement = StockMovement(
                stock_item_id=stock.id,
                movement_type=reason,
                quantity=diff,
                unit_cost=stock.average_cost or stock.unit_cost,
                total_cost=(stock.average_cost or stock.unit_cost) * abs(diff),
                notes=notes or f"Ajuste manual: {stock.current_quantity} → {new_quantity}",
                performed_by=performed_by,
            )
            self.db.add(movement)

        stock.current_quantity = new_quantity
        self.db.commit()
        self.db.refresh(stock)
        return stock

    # ── Alerts ────────────────────────────────────────────────

    def get_low_stock_items(self) -> List[StockItem]:
        """Get all items below minimum stock level."""
        return self.db.query(StockItem).filter(
            StockItem.status == "active",
            StockItem.current_quantity <= StockItem.minimum_stock,
            StockItem.minimum_stock > 0,
        ).order_by(
            (StockItem.current_quantity / func.nullif(StockItem.minimum_stock, 0)).asc()
        ).all()

    def get_expiring_items(self, days: int = 15) -> List[StockItem]:
        """Get items expiring within the next N days."""
        cutoff = date.today() + timedelta(days=days)
        return self.db.query(StockItem).filter(
            StockItem.status == "active",
            StockItem.expiry_date.isnot(None),
            StockItem.expiry_date <= cutoff,
            StockItem.expiry_date >= date.today(),
        ).order_by(StockItem.expiry_date).all()

    def get_unavailable_products(self) -> List[Product]:
        """Get products that can't be made due to insufficient stock."""
        unavailable = []
        recipes = self.db.query(ProductRecipe).all()
        for recipe in recipes:
            items = self.db.query(ProductRecipeItem).filter(
                ProductRecipeItem.recipe_id == recipe.id
            ).all()
            for ri in items:
                stock = self.db.query(StockItem).filter(
                    StockItem.id == ri.stock_item_id
                ).first()
                if stock and stock.current_quantity < ri.quantity_required:
                    product = self.db.query(Product).filter(
                        Product.id == recipe.product_id
                    ).first()
                    if product and product not in unavailable:
                        unavailable.append(product)
                    break
        return unavailable
