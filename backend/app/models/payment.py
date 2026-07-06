from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    monthly_account_id = Column(Integer, ForeignKey("monthly_accounts.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50), default="cash")  # cash, credit, debit, pix, transfer
    paid_at = Column(DateTime, default=func.now())
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    monthly_account = relationship("MonthlyAccount")
    client = relationship("Client")
    user = relationship("User")
