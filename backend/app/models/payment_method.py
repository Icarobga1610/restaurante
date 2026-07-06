from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class PaymentMethod(Base):
    """Forma de pagamento aceita pelo restaurante."""
    __tablename__ = "payment_methods"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
