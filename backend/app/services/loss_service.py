from typing import Optional
from sqlalchemy.orm import Session
from app.models.loss_record import LossRecord
from app.models.stock_item import StockItem
from app.models.stock_movement import StockMovement
from app.models.product import Product
from app.services.audit_service import AuditService


class LossService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    def register_loss(
        self,
        data: dict,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
    ) -> LossRecord:
        if not data.get("reason") or len(data["reason"].strip()) < 3:
            raise ValueError("Perda exige um motivo com pelo menos 3 caracteres")

        loss = LossRecord(
            stock_item_id=data.get("stock_item_id"),
            product_id=data.get("product_id"),
            quantity=data["quantity"],
            unit_measure=data.get("unit_measure", "unidade"),
            estimated_cost=data.get("estimated_cost", 0.0),
            loss_type=data["loss_type"],
            reason=data["reason"],
            user_id=user_id,
        )

        # Deduct stock if stock_item_id is provided
        if loss.stock_item_id:
            stock = self.db.query(StockItem).filter(
                StockItem.id == loss.stock_item_id
            ).first()
            if stock:
                stock.current_quantity -= loss.quantity
                movement = StockMovement(
                    stock_item_id=stock.id,
                    movement_type="perda",
                    quantity=-loss.quantity,
                    unit_cost=loss.estimated_cost or stock.average_cost or stock.unit_cost,
                    total_cost=(loss.estimated_cost or stock.average_cost or stock.unit_cost) * loss.quantity,
                    notes=f"Perda: {loss.reason}",
                    performed_by=user_id,
                )
                self.db.add(movement)

        self.db.add(loss)
        self.db.commit()
        self.db.refresh(loss)

        self.audit.log(
            action="create",
            entity_type="loss_record",
            entity_id=loss.id,
            user_id=user_id,
            username=username,
            details=f"Perda registrada: {loss.loss_type} - qtd {loss.quantity} - motivo: {loss.reason}",
        )
        return loss
