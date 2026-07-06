from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Signature(Base):
    __tablename__ = "signatures"

    id = Column(Integer, primary_key=True, index=True)
    monthly_account_id = Column(Integer, ForeignKey("monthly_accounts.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    signature_data = Column(Text, nullable=False)  # base64 PNG
    signed_value = Column(Float, nullable=False)
    signed_at = Column(DateTime, default=func.now())
    ip_address = Column(String(45), nullable=True)
    device_info = Column(String(255), nullable=True)
    verification_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=func.now())

    client = relationship("Client")
    user = relationship("User")
