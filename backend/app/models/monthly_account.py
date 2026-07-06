from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class MonthlyAccount(Base):
    __tablename__ = "monthly_accounts"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    month = Column(Integer, nullable=False)  # 1-12
    year = Column(Integer, nullable=False)
    total = Column(Float, default=0.0)
    status = Column(String(30), default="open")  # open, closed, confirmed_by_biometrics, paid, overdue
    closed_at = Column(DateTime, nullable=True)
    closed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    biometric_verification_id = Column(Integer, nullable=True)
    biometric_verified_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    paid_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    client = relationship("Client")
    closer = relationship("User", foreign_keys=[closed_by])
    payer = relationship("User", foreign_keys=[paid_by])
    items = relationship("MonthlyAccountItem", back_populates="account", cascade="all, delete-orphan")


class MonthlyAccountItem(Base):
    __tablename__ = "monthly_account_items"

    id = Column(Integer, primary_key=True, index=True)
    monthly_account_id = Column(Integer, ForeignKey("monthly_accounts.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    order_total = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())

    account = relationship("MonthlyAccount", back_populates="items")
    order = relationship("Order")
