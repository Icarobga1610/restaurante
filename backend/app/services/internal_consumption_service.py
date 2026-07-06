from typing import Optional
from sqlalchemy.orm import Session
from app.models.internal_consumption import InternalConsumption
from app.models.stock_item import StockItem
from app.models.stock_movement import StockMovement
from app.models.product import Product
from app.models.product_recipe import ProductRecipe, ProductRecipeItem
from app.services.audit_service import AuditService


class InternalConsumptionService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    def register(
        self,
        data: dict,
        created_by_user_id: int,
        created_by_username: str,
    ) -> InternalConsumption:
        if not data.get("reason") or len(data["reason"].strip()) < 3:
            raise ValueError("Consumo interno exige um motivo com pelo menos 3 caracteres")
        if not data.get("authorized_by_user_id"):
            raise ValueError("Consumo interno precisa de um usuário autorizador")

        consumption = InternalConsumption(
            consumption_type=data["consumption_type"],
            client_id=data.get("client_id"),
            employee_name=data.get("employee_name"),
            product_id=data["product_id"],
            quantity=data["quantity"],
            estimated_cost=data.get("estimated_cost", 0.0),
            reason=data["reason"],
            authorized_by_user_id=data["authorized_by_user_id"],
            created_by_user_id=created_by_user_id,
        )

        # Deduct stock using recipe if available
        recipe = self.db.query(ProductRecipe).filter(
            ProductRecipe.product_id == consumption.product_id
        ).first()

        if recipe:
            recipe_items = self.db.query(ProductRecipeItem).filter(
                ProductRecipeItem.recipe_id == recipe.id
            ).all()
            total_cost = 0.0
            for ri in recipe_items:
                stock = self.db.query(StockItem).filter(
                    StockItem.id == ri.stock_item_id
                ).first()
                if stock:
                    needed = ri.quantity_required * consumption.quantity
                    stock.current_quantity -= needed
                    cost = (stock.average_cost or stock.unit_cost) * needed
                    total_cost += cost
                    movement = StockMovement(
                        stock_item_id=stock.id,
                        movement_type="consumo_interno",
                        quantity=-needed,
                        unit_cost=stock.average_cost or stock.unit_cost,
                        total_cost=cost,
                        notes=f"{consumption.consumption_type}: {consumption.reason}",
                        performed_by=created_by_user_id,
                    )
                    self.db.add(movement)
            consumption.estimated_cost = round(total_cost, 2)

        self.db.add(consumption)
        self.db.commit()
        self.db.refresh(consumption)

        self.audit.log(
            action="create",
            entity_type="internal_consumption",
            entity_id=consumption.id,
            user_id=created_by_user_id,
            username=created_by_username,
            details=f"Cortesia/consumo interno: {consumption.consumption_type} - {consumption.reason}",
        )
        return consumption
