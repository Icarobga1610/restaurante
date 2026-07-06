from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class CashRegister(Base):
    """Caixa diário do restaurante."""
    __tablename__ = "cash_registers"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True, index=True)
    opening_balance = Column(Float, default=0.0)
    expected_closing = Column(Float, default=0.0)
    informed_closing = Column(Float, nullable=True)
    difference = Column(Float, nullable=True)
    status = Column(String(20), default="open")  # open, closed
    opened_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    closed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    opened_at = Column(DateTime, default=func.now())
    closed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    opener = relationship("User", foreign_keys=[opened_by])
    closer = relationship("User", foreign_keys=[closed_by])
    movements = relationship("CashMovement", back_populates="cash_register", cascade="all, delete-orphan")


class CashMovement(Base):
    """Movimentação financeira do caixa."""
    __tablename__ = "cash_movements"

    id = Column(Integer, primary_key=True, index=True)
    cash_register_id = Column(Integer, ForeignKey("cash_registers.id"), nullable=False, index=True)
    movement_type = Column(String(30), nullable=False)
    # venda_dinheiro, venda_pix, venda_cartao, pagamento_conta_mensal,
    # sangria, suprimento, despesa, ajuste
    description = Column(String(255), nullable=True)
    amount = Column(Float, nullable=False)  # positive = in, negative = out
    payment_method = Column(String(30), nullable=True)
    reference_id = Column(Integer, nullable=True)
    reference_type = Column(String(50), nullable=True)
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now(), index=True)

    cash_register = relationship("CashRegister", back_populates="movements")
    performer = relationship("User")
