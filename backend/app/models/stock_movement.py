from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class StockMovement(Base):
    """Movimentação de estoque (entrada, saída, ajuste, perda, etc)."""
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    stock_item_id = Column(Integer, ForeignKey("stock_items.id"), nullable=False, index=True)
    movement_type = Column(String(30), nullable=False)
    # entrada_compra, saida_venda, ajuste_manual, perda, devolucao, transferencia, consumo_interno
    quantity = Column(Float, nullable=False)  # positive for in, negative for out
    unit_cost = Column(Float, nullable=True)
    total_cost = Column(Float, nullable=True)
    reference_id = Column(Integer, nullable=True)  # order_id, purchase_id, etc
    reference_type = Column(String(50), nullable=True)  # order, purchase, adjustment
    notes = Column(Text, nullable=True)
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now(), index=True)

    stock_item = relationship("StockItem")
    performer = relationship("User")
