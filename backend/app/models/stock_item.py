from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class StockItem(Base):
    """Insumo / matéria-prima do restaurante."""
    __tablename__ = "stock_items"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), nullable=True, unique=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    category = Column(String(80), nullable=True)  # hortifruti, carnes, bebidas, limpeza, descartaveis, etc
    unit_measure = Column(String(20), nullable=False, default="unidade")  # kg, g, litro, ml, unidade, pacote, caixa
    current_quantity = Column(Float, default=0.0)
    minimum_stock = Column(Float, default=0.0)
    unit_cost = Column(Float, default=0.0)
    average_cost = Column(Float, default=0.0)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    expiry_date = Column(Date, nullable=True)
    status = Column(String(20), default="active")  # active, inactive
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    supplier = relationship("Supplier")
