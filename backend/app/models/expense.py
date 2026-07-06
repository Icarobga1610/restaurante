from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Expense(Base):
    """Despesa do restaurante."""
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)
    # aluguel, energia, agua, internet, salarios, manutencao,
    # compra_emergencial, marketing, imposto, outros
    amount = Column(Float, nullable=False)
    expense_date = Column(Date, nullable=False, index=True)
    payment_method = Column(String(30), default="cash")
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())

    supplier = relationship("Supplier")
    creator = relationship("User")
