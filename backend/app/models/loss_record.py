from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class LossRecord(Base):
    """Registro de perda de insumo ou produto."""
    __tablename__ = "loss_records"

    id = Column(Integer, primary_key=True, index=True)
    stock_item_id = Column(Integer, ForeignKey("stock_items.id"), nullable=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    quantity = Column(Float, nullable=False)
    unit_measure = Column(String(20), nullable=False, default="unidade")
    estimated_cost = Column(Float, default=0.0)
    loss_type = Column(String(30), nullable=False)
    # vencimento, quebra, erro_preparo, devolucao, consumo_interno, cortesia, ajuste_estoque, outro
    reason = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())

    stock_item = relationship("StockItem")
    product = relationship("Product")
    user = relationship("User")
