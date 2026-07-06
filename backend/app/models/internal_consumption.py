from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class InternalConsumption(Base):
    """Registro de cortesia e consumo interno."""
    __tablename__ = "internal_consumptions"

    id = Column(Integer, primary_key=True, index=True)
    consumption_type = Column(String(30), nullable=False)
    # cortesia_cliente, consumo_funcionario, degustacao, brinde, promocional, consumo_interno
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    employee_name = Column(String(150), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False, default=1.0)
    estimated_cost = Column(Float, default=0.0)
    reason = Column(Text, nullable=False)
    authorized_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())

    client = relationship("Client")
    product = relationship("Product")
    authorized_by = relationship("User", foreign_keys=[authorized_by_user_id])
    created_by = relationship("User", foreign_keys=[created_by_user_id])
