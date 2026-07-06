from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Purchase(Base):
    """Compra de insumos para o restaurante."""
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    purchase_date = Column(DateTime, default=func.now())
    invoice_number = Column(String(50), nullable=True)
    total_cost = Column(Float, default=0.0)
    payment_method = Column(String(30), default="cash")  # cash, credit, debit, pix, transfer
    status = Column(String(30), default="planned")  # planned, received, cancelled
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    supplier = relationship("Supplier")
    creator = relationship("User")
    items = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")


class PurchaseItem(Base):
    """Item de uma compra."""
    __tablename__ = "purchase_items"

    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id"), nullable=False)
    stock_item_id = Column(Integer, ForeignKey("stock_items.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_cost = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())

    purchase = relationship("Purchase", back_populates="items")
    stock_item = relationship("StockItem")
